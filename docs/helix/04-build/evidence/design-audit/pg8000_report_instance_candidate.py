"""Private report-only driver experiment; no native/account/publication admission."""
from pg8000_instance_candidate import FrameFile, SuppliedSocket, RawConnection
from python_pg_receive_candidate import Receiver
from python_report_frame_candidate import described_report_cell


class ReportFrameFile(FrameFile):
    def __init__(self, transport):
        super().__init__(transport)
        # Separate initial experimental bounds, before any ingress or sender use.
        self.receiver = Receiver(transport, frame_bytes=4194315, total_bytes=16777216,
                                 messages=100, reads=10000)
        self.remaining_send_bytes = 8388608


class ReportSocket(SuppliedSocket):
    def __init__(self, transport):
        self.transport = transport
        self.file = ReportFrameFile(transport)
        self.opened = False


class ReportConnection(RawConnection):
    def handle_ROW_DESCRIPTION(self, data, context):
        super().handle_ROW_DESCRIPTION(data, context)
        if len(context.columns) != 1 or context.columns[0].type_oid != 25:
            raise ValueError('Single text report descriptor required')
        self.report_descriptor = self.original_frame(b'T', data)

    def handle_DATA_ROW(self, data, context):
        if context.columns is None or context.rows is None or len(context.rows) != 0:
            raise ValueError('Exactly one original report row required')
        cell = described_report_cell(self.report_descriptor, self.original_frame(b'D', data))
        context.rows.append((cell,))
