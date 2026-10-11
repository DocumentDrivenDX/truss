"""Original borrowed driver hooks; restoration performs no native I/O."""

class DriverAttachment:
    def __init__(self):
        self.connection=None
        self.boundary=None
        self.originals=()
        self.updates=()
        self.handlers=None
        self.dispatch_table=None
        self.hooks=None
        self.phase='unattached'
        self.attempted=[]

    def prepare(self,connection,boundary,hooks,updates):
        if self.phase!='unattached':raise ValueError('One original attachment required')
        self.connection=connection
        self.boundary=boundary
        self.handlers=dict(connection.message_types)
        self.dispatch_table=connection.message_types
        self.hooks=dict(hooks)
        self.originals=tuple((name,name in connection.__dict__,connection.__dict__.get(name))
                             for name,_ in updates)
        self.updates=updates
        boundary._borrowed_attachment=self
        self.phase='prepared'

    def _publish(self,name,callback):
        self.attempted.append(name)
        callback()

    def install(self):
        self.phase='installing'
        # Publish original custody before changing any driver hook. A later
        # restoration failure leaves this marker blocking accidental reuse.
        name,value=self.updates[0]
        self._publish(name,lambda:setattr(self.connection,name,value))
        self._publish('handlers',lambda:self.connection.message_types.update(self.hooks))
        for name,value in self.updates[1:]:
            self._publish(name,lambda name=name,value=value:setattr(self.connection,name,value))
        self.phase='attached'

    def restore(self):
        if self.phase in ('unattached','detached'):return True
        con=self.connection
        if con.message_types is not self.dispatch_table:
            self.phase='unresolved';return False
        # Never overwrite a foreign replacement, including unmodified handlers.
        for code,original in self.handlers.items():
            current=con.message_types.get(code)
            if current is not original and current is not self.hooks.get(code):
                self.phase='unresolved';return False
        if set(con.message_types)!=set(self.handlers):
            self.phase='unresolved';return False
        for (name,present,original),(_,owned) in zip(self.originals,self.updates):
            current=con.__dict__.get(name)
            if name in con.__dict__ and current is not owned and (not present or current is not original):
                self.phase='unresolved';return False
            if name not in con.__dict__ and present:
                self.phase='unresolved';return False
        try:
            con.message_types.update(self.handlers)
            for name,present,original in reversed(self.originals):
                if present:setattr(con,name,original)
                elif name in con.__dict__:delattr(con,name)
        except BaseException:
            self.phase='unresolved'
            raise
        self.phase='detached'
        return True
