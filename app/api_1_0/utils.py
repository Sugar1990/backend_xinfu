import threading


def success_res(data={}, msg=""):
    return {"code": 1, "msg": msg, "data": data}


def fail_res(msg=""):
    return {"code": 0, "msg": msg}


class RWLock(object):
    # __instance = None
    #
    # def __new__(cls, *args, **kwargs):
    #     if not cls.__instance:
    #         cls.__instance = object.__new__(cls, *args, **kwargs)
    #     return cls.__instance

    def __init__(self):
        self.lock = threading.Lock()
        self.w_cond = threading.Condition(self.lock)
        self.w_waiter = 0  # 等待写锁的线程数
        self.r_cond = threading.Condition(self.lock)
        self.r_waiter = 0  # 等待读锁的线程数
        self.state = 0  # 正数：正在读操作的线程数；负数；正在写操作的线程数
        self.owners = []
        self.w_first = True  # True写优先，False读优先

    def write_acquire(self, blocking=True):
        print("write_acquire", flush=True)
        me = threading.get_ident()
        with self.lock:
            while not self._write_acquire(me):
                if not blocking:
                    return False
                self.w_waiter += 1
                self.w_cond.wait()
                self.w_waiter -= 1
        return True

    # 获取写锁，只有当锁没有占用，或者当前线程已经占用
    def _write_acquire(self, me):
        if self.state == 0 or (self.state < 0 and me in self.owners):
            self.state -= 1
            self.owners.append(me)
            return True
        if self.state > 0 and me in self.owners:
            raise RuntimeError("cannot recursively wlock a rdlocked lock")
        return False

    def read_acquire(self, blocking=True):
        print("read_acquire", flush=True)
        me = threading.get_ident()
        with self.lock:
            while not self._read_acquire(me):
                if not blocking:
                    return False
                self.r_waiter += 1
                self.r_cond.wait()
                self.r_waiter -= 1
        return True

    def _read_acquire(self, me):
        if self.state < 0:
            print("读操作被写锁占用")
            # 如果锁被写锁占用
            return False
        if not self.w_waiter:
            flag = True
        else:
            flag = me in self.owners
        if flag or not self.w_first:
            self.state += 1
            self.owners.append(me)
            return True
        return False

    def unlock(self):
        me = threading.get_ident()
        with self.lock:
            try:
                self.owners.remove(me)
            except:
                raise RuntimeError('cannot release un-acquire lock')

            if self.state > 0:
                self.state -= 1
            else:
                self.state += 1

            if not self.state:
                # 如果有写操作在等待，且默认写优先
                if self.w_waiter and self.w_first:
                    self.w_cond.notify()
                elif self.r_waiter:
                    self.r_cond.notify_all()
                elif self.w_waiter:
                    self.w_cond.notify()

    read_release = unlock
    write_release = unlock
