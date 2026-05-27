from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6 import QtCore

from .models import AccountRecord
from .services import MailService
from .storage import AccountStore


class FetchWorker(QtCore.QThread):
    status_changed = QtCore.pyqtSignal(str)
    progress_changed = QtCore.pyqtSignal(int, int, str, int)
    results_ready = QtCore.pyqtSignal(object)
    log_message = QtCore.pyqtSignal(str)
    accounts_changed = QtCore.pyqtSignal()
    finished_summary = QtCore.pyqtSignal(int, int, int, bool)

    def __init__(
        self,
        service: MailService,
        account_store: AccountStore,
        accounts: list[AccountRecord],
        protocol: str,
        top: int,
        concise_mode: bool,
    ) -> None:
        super().__init__()
        self.service = service
        self.account_store = account_store
        self.accounts = accounts
        self.protocol = protocol
        self.top = top
        self.concise_mode = concise_mode
        self.stop_requested = threading.Event()

    def request_stop(self) -> None:
        self.stop_requested.set()

    def run(self) -> None:
        success = total = completed = 0
        status_changed = False
        stopped = False
        if not self.accounts:
            self.status_changed.emit("没有可取件账号")
            self.finished_summary.emit(0, 0, 0, False)
            return

        try:
            if self.protocol != "IMAP":
                self.service.ensure_graph()

            self.status_changed.emit(f"取件中 0/{len(self.accounts)}")
            with ThreadPoolExecutor(max_workers=min(12, len(self.accounts))) as executor:
                futures = {
                    executor.submit(self.service.fetch_account_rows, account, self.protocol, self.top, self.concise_mode): account
                    for account in self.accounts
                }
                for future in as_completed(futures):
                    account = futures[future]
                    completed += 1
                    if self.stop_requested.is_set():
                        for pending in futures:
                            pending.cancel()
                        self.log_message.emit("已停止，剩余邮箱未继续取件。")
                        stopped = True
                        break
                    try:
                        rows = future.result()
                        success += 1
                        total += len(rows)
                        self.account_store.mark(account.email, f"成功 {len(rows)} 封", fetched=True, save=False)
                        status_changed = True
                        self.results_ready.emit(rows)
                        self.log_message.emit(f"{account.email} 获取成功：{len(rows)} 封。")
                    except Exception as exc:
                        self.account_store.mark(account.email, "获取失败", save=False)
                        status_changed = True
                        self.log_message.emit(f"{account.email} 获取失败：{exc}")
                    self.progress_changed.emit(completed, len(self.accounts), account.email, total)
                    self.status_changed.emit(f"取件中 {completed}/{len(self.accounts)} | {total} 封")
        finally:
            if status_changed:
                try:
                    self.account_store.save()
                except Exception as exc:
                    self.log_message.emit(f"保存账号状态失败：{exc}")
            self.accounts_changed.emit()
            self.finished_summary.emit(success, len(self.accounts), total, stopped)
