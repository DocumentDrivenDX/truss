# SPDX-License-Identifier: MIT OR Apache-2.0
"""Inspect PostgreSQL through public Truss APIs without ending a host transaction.

The command uses libpq PGHOST/PGPORT/PGUSER/PGDATABASE settings.
The snapshot is diagnostic; readiness remains unverified.
"""
from dataclasses import asdict
import json

import psycopg
from truss import (
    INSPECTION_ASSEMBLY_PROFILE,
    AssemblyConstructionError,
    InstallationObservation,
    Outcome,
    PsycopgHost,
    TransactionHandle,
    InstallationInspectionConfiguration,
    Ok,
    adopt_psycopg_host,
    create_reference_assembly,
)


def inspect_transaction(
    host: PsycopgHost, transaction: TransactionHandle
) -> Outcome[InstallationObservation] | AssemblyConstructionError:
    """Return the public outcome; the caller retains transaction ownership."""
    constructed = create_reference_assembly(
        InstallationInspectionConfiguration(
            assembly_id="installation-inspection-example",
            assembly_profile=INSPECTION_ASSEMBLY_PROFILE,
        ),
        host,
    )
    if not isinstance(constructed, Ok):
        return constructed
    assembly = constructed.value
    try:
        return assembly.inspect_installation(transaction)
    finally:
        assembly.dispose()


def main():
    with psycopg.connect(
        autocommit=True, options="-c statement_timeout=10000"
    ) as connection:
        host = adopt_psycopg_host(connection)
        try:
            connection.execute("BEGIN READ ONLY")
            adopted = host.adopt_transaction(access_mode="read_only")
            if not isinstance(adopted, Ok):
                raise RuntimeError(adopted.error.code)
            observation = inspect_transaction(host, adopted.value)
            if not isinstance(observation, Ok):
                error = getattr(observation, "error", observation)
                raise RuntimeError(error.code)
            print(json.dumps(asdict(observation.value), indent=2))
        finally:
            # This command owns the transaction; the embedding helper does not.
            connection.rollback()
            host.detach()


if __name__ == "__main__":
    main()
