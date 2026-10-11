
import hashlib
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.identity_connection import (
    IdentityBase,
    identity_engine,
    get_identity_db,
)
from app.database.identity_models import (
    BlockchainLedgerBlock,
    RegistryDocumentAudit,
)

# Ensure the ledger table exists in the identity registry database.
IdentityBase.metadata.create_all(bind=identity_engine)

router = APIRouter(
    prefix="/registry/blockchain",
    tags=["Blockchain Ledger"],
)

GENESIS_HASH = "0" * 64


def format_timestamp(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def calculate_block_hash(
    block_index: int,
    audit_id: int,
    audit_hash: str,
    timestamp: str,
    previous_block_hash: str,
) -> str:
    payload = {
        "block_index": block_index,
        "audit_id": audit_id,
        "audit_hash": audit_hash,
        "timestamp": timestamp,
        "previous_block_hash": previous_block_hash,
    }
    canonical_data = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_data.encode("utf-8")).hexdigest()


@router.post("/append/{audit_id}")
def append_audit_to_ledger(
    audit_id: int,
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    audit = db.query(RegistryDocumentAudit).filter(
        RegistryDocumentAudit.id == audit_id
    ).first()

    if audit is None:
        raise HTTPException(404, "Audit record not found.")

    if not audit.audit_hash:
        raise HTTPException(
            409,
            "This legacy audit has no SHA-256 hash and cannot be appended.",
        )

    existing = db.query(BlockchainLedgerBlock).filter(
        BlockchainLedgerBlock.audit_id == audit_id
    ).first()

    if existing:
        raise HTTPException(
            409,
            {
                "message": "This audit is already in the ledger.",
                "block_index": existing.block_index,
                "block_hash": existing.block_hash,
            },
        )

    last_block = (
        db.query(BlockchainLedgerBlock)
        .order_by(BlockchainLedgerBlock.block_index.desc())
        .first()
    )

    block_index = 1 if last_block is None else last_block.block_index + 1
    previous_hash = (
        GENESIS_HASH if last_block is None else last_block.block_hash
    )

    timestamp = datetime.utcnow()
    timestamp_string = format_timestamp(timestamp)

    block_hash = calculate_block_hash(
        block_index=block_index,
        audit_id=audit.id,
        audit_hash=audit.audit_hash,
        timestamp=timestamp_string,
        previous_block_hash=previous_hash,
    )

    block = BlockchainLedgerBlock(
        block_index=block_index,
        audit_id=audit.id,
        audit_hash=audit.audit_hash,
        timestamp=timestamp,
        previous_block_hash=previous_hash,
        block_hash=block_hash,
    )

    try:
        db.add(block)
        db.commit()
        db.refresh(block)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            "The audit may already have been appended by another request.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(500, "Could not save the ledger block.")

    return {
        "message": "Audit appended to the local hash-linked ledger.",
        "block_index": block.block_index,
        "audit_id": block.audit_id,
        "audit_hash": block.audit_hash,
        "timestamp": format_timestamp(block.timestamp),
        "previous_block_hash": block.previous_block_hash,
        "block_hash": block.block_hash,
    }


@router.get("/blocks")
def list_ledger_blocks(
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    blocks = (
        db.query(BlockchainLedgerBlock)
        .order_by(BlockchainLedgerBlock.block_index.asc())
        .all()
    )

    return [
        {
            "block_index": block.block_index,
            "audit_id": block.audit_id,
            "audit_hash": block.audit_hash,
            "timestamp": format_timestamp(block.timestamp),
            "previous_block_hash": block.previous_block_hash,
            "block_hash": block.block_hash,
        }
        for block in blocks
    ]


@router.get("/verify")
def verify_ledger(
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    blocks = (
        db.query(BlockchainLedgerBlock)
        .order_by(BlockchainLedgerBlock.block_index.asc())
        .all()
    )

    issues = []
    expected_previous_hash = GENESIS_HASH

    for expected_index, block in enumerate(blocks, start=1):
        timestamp_string = format_timestamp(block.timestamp)

        if block.block_index != expected_index:
            issues.append({
                "block_index": block.block_index,
                "issue": "BLOCK_INDEX_SEQUENCE_INVALID",
            })

        if block.previous_block_hash != expected_previous_hash:
            issues.append({
                "block_index": block.block_index,
                "issue": "PREVIOUS_HASH_MISMATCH",
            })

        recalculated_hash = calculate_block_hash(
            block_index=block.block_index,
            audit_id=block.audit_id,
            audit_hash=block.audit_hash,
            timestamp=timestamp_string,
            previous_block_hash=block.previous_block_hash,
        )

        if recalculated_hash != block.block_hash:
            issues.append({
                "block_index": block.block_index,
                "issue": "BLOCK_HASH_MISMATCH",
            })

        audit = db.query(RegistryDocumentAudit).filter(
            RegistryDocumentAudit.id == block.audit_id
        ).first()

        if audit is None:
            issues.append({
                "block_index": block.block_index,
                "issue": "AUDIT_RECORD_MISSING",
            })
        elif audit.audit_hash != block.audit_hash:
            issues.append({
                "block_index": block.block_index,
                "issue": "AUDIT_HASH_DIFFERS_FROM_LEDGER",
            })

        expected_previous_hash = block.block_hash

    return {
        "chain_valid": len(issues) == 0,
        "blocks_checked": len(blocks),
        "issues": issues,
        "message": (
            "Ledger integrity verified."
            if not issues
            else "Ledger integrity check found issues."
        ),
        "note": (
            "This is a local hash-linked ledger, not a distributed "
            "blockchain. Database access controls and external backups "
            "are still needed to protect against deliberate rewriting."
        ),
    }
