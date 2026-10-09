"""Request-scoped ORM isolation shared by legacy and revision 4 resources."""

from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker, with_loader_criteria

from devai.models import User
from devai.models.studio import LEGACY_WORKSPACE, Membership, Workspace


def scoped_factory(factory, workspace_id):
    return sessionmaker(bind=factory.kw["bind"], info={"workspace_id": workspace_id})


def resolve_workspace(request, principal):
    factory = request.app.state.session_factory
    requested = request.headers.get("X-Workspace-ID")
    with factory.begin() as db:
        if principal["id"] == "development":
            workspace_id = requested or LEGACY_WORKSPACE
            if not db.get(Workspace, workspace_id):
                raise HTTPException(404, "Workspace not found")
            role, publish = "owner", True
        else:
            # Concurrent first-page requests must adopt an account exactly once.
            # Lock its global identity before checking memberships; do not retry a
            # failed insert inside an aborted PostgreSQL transaction.
            user = db.query(User).filter_by(id=principal["id"]).with_for_update().first()
            if not user or not user.active:
                raise HTTPException(401, "Session expired; sign in again")
            memberships = db.query(Membership).filter_by(user_id=principal["id"]).all()
            if not memberships:
                # Users provisioned by the preserved local account API join the original studio.
                membership = Membership(
                    workspace_id=LEGACY_WORKSPACE,
                    user_id=principal["id"],
                    role="owner" if principal["role"] == "admin" else principal["role"],
                    publish_permission=int(principal["role"] in {"admin", "reviewer"}),
                )
                db.add(membership)
                memberships = [membership]
            member = (
                next((item for item in memberships if item.workspace_id == requested), None)
                if requested
                else memberships[0]
            )
            if not member:
                raise HTTPException(404, "Workspace not found")
            workspace_id, role, publish = (
                member.workspace_id,
                member.role,
                bool(member.publish_permission),
            )
    request.state.workspace_id = workspace_id
    principal.update(workspace_id=workspace_id, workspace_role=role, publish_permission=publish)
    # Legacy singleton settings/admin controls only manage the adopted original studio.
    if workspace_id != LEGACY_WORKSPACE and request.url.path.startswith(("/ops", "/auth/users")):
        raise HTTPException(403, "Use workspace-scoped settings and members")
    return principal


@event.listens_for(Session, "do_orm_execute")
def isolate_reads(execute_state):
    workspace_id = execute_state.session.info.get("workspace_id")
    if not workspace_id or not execute_state.is_orm_statement:
        return
    from devai.core.database import Base

    statement = execute_state.statement
    for mapper in Base.registry.mappers:
        model = mapper.class_
        if hasattr(model, "workspace_id"):
            statement = statement.options(
                with_loader_criteria(
                    model, model.workspace_id == workspace_id, include_aliases=True
                )
            )
    execute_state.statement = statement


@event.listens_for(Session, "before_flush")
def isolate_writes(session, _context, _instances):
    workspace_id = session.info.get("workspace_id")
    if not workspace_id:
        return
    for item in session.new | session.dirty | session.deleted:
        if hasattr(item, "workspace_id"):
            if item in session.new and item.workspace_id is None:
                item.workspace_id = workspace_id
            elif item.workspace_id != workspace_id:
                raise HTTPException(404, "Resource not found")
