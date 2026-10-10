"""Local payload-accounted seam; core/parser/transport overhead remains open."""
from truss._accounted_receive import AccountedReceiver
from pg8000_instance_candidate import FrameFile, SuppliedSocket


class AccountedFrameFile(FrameFile):
    def __init__(self, transport, account, producer):
        super().__init__(transport)
        self.account, self.producer = account, producer
        self.receiver = AccountedReceiver(transport, account, producer,
            frame_bytes=1048576, total_bytes=16777216, messages=100, reads=10000)

    def read(self, size):
        if self.closed:
            raise ValueError('Closed accounted experiment file')
        try:
            if self.pending is None:
                if type(size) is not int or size != 5:
                    raise ValueError('Original five-byte header request required')
                self.header, self.pending = self.receiver.receive_parts()
                self.message_sizes.append([self.header[:1].decode('ascii'),5+len(self.pending)])
                return self.header
            if type(size) is not int or size != len(self.pending):
                raise ValueError('Original complete body request required')
            result = self.pending
            self.pending = None
            return result
        except BaseException:
            self.close()
            raise

    def write(self, source):
        try:
            return super().write(source)
        except BaseException:
            self.close()
            raise

    def close(self):
        super().close()
        self.account.close(self.producer)


class AccountedSocket(SuppliedSocket):
    def __init__(self, transport, account, producer):
        self.transport = transport
        self.file = AccountedFrameFile(transport,account,producer)
        self.opened = False

    def close(self):
        try:
            self.file.close()
        finally:
            self.transport.close()
