# -*- coding: utf-8 -*-

##############################################################################
#Author：QQ173782910
##############################################################################

import json
import sys
import traceback
import socket
from datetime import datetime
from time import sleep
from threading import Lock,Thread
import websocket

class BaseWebsocket(object):
    def __init__(self,host=None, ping_interval= 10):
        self.host = host
        self.ping_interval = ping_interval

        self._ws_lock = Lock()
        self._ws = None

        self._worker_thread = None
        self._ping_thread = None
        self._active = False

        # debug需要..
        self._last_sent_text = None
        self._last_received_text = None

    def start(self):
        """q启用客户端，连接成功之后会调用on——open这个方法。之后才调用向服务器发送消息的方法"""
        self._active = True
        self._worker_thread = Thread(target=self._run)   #调用保持运行函数，之前已经定义self.woruthread为None
        self._worker_thread.start()

        self._ping_thread = Thread(target=self._run_ping)
        self._ping_thread.start()

    def stop(self):
        self._active = False
        self._disconnect()

    def join(self):
        self._ping_thread.join()
        self._worker_thread.join()

    def send_msg(self, msg:dict):
        text = json.dumps(msg)
        self._record_last_sent_text(text)
        return self._send_text(text)

    def _send_text(self, text:str):
        ws = self._ws
        if ws:
            ws.send(text, opcode = websocket.ABNF.OPCODE_TEXT)

    def _ensure_connection(self):
        """"""
        triggered = False
        with self._ws_lock:
            if self._ws is None:
                self._ws = websocket.create_connection(self.host)

                triggered = True
        if triggered:
            self.on_open()

    def _disconnect(self):
        """
        """
        triggered = False
        with self._ws_lock:
            if self._ws:
                ws: websocket.WebSocket = self._ws
                self._ws = None

                triggered = True
        if triggered:
            ws.close()
            self.on_close()


    def _run(self):
        """
        保持运行，知道stop方法调用.
        """
        try:
            while self._active:
                try:
                    self._ensure_connection()
                    ws = self._ws
                    if ws:
                        text = ws.recv()

                        # ws object is closed when recv function is blocking
                        if not text:
                            self._disconnect()
                            continue

                        self._record_last_received_text(text)

                        self.on_msg(text)
                # ws is closed before recv function is called
                # For socket.error, see Issue #1608
                except (websocket.WebSocketConnectionClosedException, socket.error):
                    self._disconnect()

                # other internal exception raised in on_msg
                except:  # noqa
                    et, ev, tb = sys.exc_info()
                    self.on_error(et, ev, tb)
                    self._disconnect()  #

        except:  # noqa
            et, ev, tb = sys.exc_info()
            self.on_error(et, ev, tb)

        self._disconnect()


    def _run_ping(self):
        """"""
        while self._active:
            try:
                self._ping()
            except:  # noqa
                et, ev, tb = sys.exc_info()
                self.on_error(et, ev, tb)
                sleep(1)

            for i in range(self.ping_interval):
                if not self._active:
                    break
                sleep(1)


    def _ping(self):
        """"""
        ws = self._ws
        if ws:
            ws.send("ping", websocket.ABNF.OPCODE_PING)


    def on_open(self):
        """on open """
        print("websocket open..")


    def on_close(self):
        """
        on close websocket
        """
        print("websocket close......")


    def on_msg(self, data: str):
        """call when the msg arrive."""
        pass

    def on_error(self, exception_type: type, exception_value: Exception, tb):
        """
        Callback when exception raised.
        """
        sys.stderr.write(
            self.exception_detail(exception_type, exception_value, tb)
        )

        return sys.excepthook(exception_type, exception_value, tb)

    def exception_detail(
            self, exception_type: type, exception_value: Exception, tb
    ):
        """
        Print detailed exception information.
        """
        text = "[{}]: Unhandled WebSocket Error:{}\n".format(
            datetime.now().isoformat(), exception_type
        )
        text += "LastSentText:\n{}\n".format(self._last_sent_text)
        text += "LastReceivedText:\n{}\n".format(self._last_received_text)
        text += "Exception trace: \n"
        text += "".join(
            traceback.format_exception(exception_type, exception_value, tb)
        )
        return text
    

    def _record_last_sent_text(self, text: str):
        """
        Record last sent text for debug purpose.
        """
        self._last_sent_text = text[:1000]


    def _record_last_received_text(self, text: str):
        """
        Record last received text for debug purpose.
        """
        self._last_received_text = text[:1000]






























