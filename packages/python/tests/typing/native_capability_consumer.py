"""Type the same capability selection used by native adopter workflows."""
from truss import (CatalogReferenceAssembly,CapabilityAvailable,TransactionHandle,
    CatalogDocument,Ok,ObjectFound,FeedPage,HistoryEntity)
from truss.capability_contracts import NativeRuntimeOperations


def consume(assembly: CatalogReferenceAssembly, transaction: TransactionHandle,
            documents: tuple[CatalogDocument,...]) -> None:
    operations: NativeRuntimeOperations = assembly
    catalog = assembly.catalog(assembly.catalog_selection)
    if isinstance(catalog,CapabilityAvailable):
        catalog.capability.report_in_transaction(transaction)
    reader = assembly.direct_reads(assembly.direct_read_selection)
    if isinstance(reader,CapabilityAvailable):
        found = reader.capability.get_object_in_transaction(transaction,
            document_id='orders',module_id='sales',record_id='Order',object_id=1)
        if isinstance(found,Ok) and isinstance(found.value,ObjectFound):
            reader.capability.page_edges_in_transaction(transaction,document_id='orders',
                module_id='sales',relationship_id='items',anchor=found.value.object.identity)
    importer = assembly.imports(assembly.import_selection,documents=documents)
    if isinstance(importer,CapabilityAvailable):
        importer.capability.import_context_in_transaction(transaction)
    feed = assembly.feed(assembly.feed_selection)
    if isinstance(feed,CapabilityAvailable):
        page = feed.capability.read_feed_in_transaction(transaction,consumer_id='warehouse')
        if isinstance(page,Ok) and isinstance(page.value,FeedPage):
            feed.capability.reread_feed_in_transaction(transaction,page.value)
            feed.capability.acknowledge_feed_in_transaction(transaction,page.value)
    reader=assembly.direct_reads(assembly.direct_read_selection)
    if isinstance(reader,CapabilityAvailable):
        reader.capability.lookup_import_source_in_transaction(transaction,entity=HistoryEntity(kind='object',document_id='orders',module_id='sales',definition_id='Order',id=1))
    operations.reader_catalog_in_transaction(transaction)
    history=assembly.history(assembly.history_selection)
    if isinstance(history,CapabilityAvailable):
        history.capability.reconstruct_in_transaction(transaction,entity=HistoryEntity(
            kind='object',document_id='orders',module_id='sales',definition_id='Order',id=1),version=1)

    queries=assembly.compiled_execution(assembly.compiled_selection)
    if isinstance(queries,CapabilityAvailable):
        queries.capability.query_in_transaction(transaction,sql='SELECT COUNT(*) AS total FROM Order o',
            document_ids=('orders',),parameters={'active':True})

        from decimal import Decimal
        queries.capability.query_in_transaction(transaction,sql='SELECT o.amount FROM Order o WHERE o.amount = :amount',
            document_ids=('orders',),parameters={'amount':Decimal('9007199254740993.123456789')})
