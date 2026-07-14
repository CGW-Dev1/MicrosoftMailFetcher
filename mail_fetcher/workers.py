from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6 import QtCore

from .models import AccountRecord
from .services import MailService
from .storage import AccountStore, PhoneStore


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
        phone_store: PhoneStore,
        accounts: list[AccountRecord],
        protocol: str,
        top: int,
        concise_mode: bool,
    ) -> None:
        super().__init__()
        self.service = service
        self.account_store = account_store
        self.phone_store = phone_store
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

        total_jobs = len(self.accounts)
        try:
            if self.protocol != "IMAP":
                self.service.ensure_graph()

            self.status_changed.emit(f"取件中 0/{total_jobs}")
            # Outlook IMAP is more sensitive to bursts of concurrent logins
            # than Graph.  A smaller pool avoids intermittent AUTH/rate-limit
            # failures when fetching many accounts at once.
            worker_limit = 5 if self.protocol == "IMAP" else 12
            with ThreadPoolExecutor(max_workers=min(worker_limit, max(1, total_jobs))) as executor:
                futures: dict[object, AccountRecord] = {}
                for account in self.accounts:
                    future = executor.submit(
                        self.service.fetch_account_rows,
                        account,
                        self.protocol,
                        self.top,
                        self.concise_mode,
                    )
                    futures[future] = account
                for future in as_completed(futures):
                    account = futures[future]
                    completed += 1
                    if self.stop_requested.is_set():
                        for pending in futures:
                            pending.cancel()
                        self.log_message.emit("已停止，剩余任务未继续取件。")
                        stopped = True
                        break
                    try:
                        rows = future.result()
                        self.account_store.mark(account.email, f"成功 {len(rows)} 封", fetched=True, save=False)
                        self.log_message.emit(f"{account.email} 获取成功：{len(rows)} 封。")
                        success += 1
                        total += len(rows)
                        status_changed = True
                        self.results_ready.emit(rows)
                    except Exception as exc:
                        detail = " ".join(str(exc).split())[:96]
                        self.account_store.mark(account.email, f"失败 · {detail}", save=False)
                        status_changed = True
                        self.log_message.emit(f"{account.email} 获取失败：{exc}")
                    self.progress_changed.emit(completed, total_jobs, account.email, total)
                    self.status_changed.emit(f"取件中 {completed}/{total_jobs} | {total} 条")
        finally:
            if status_changed:
                try:
                    self.account_store.save()
                    self.phone_store.save()
                except Exception as exc:
                    self.log_message.emit(f"保存账号状态失败：{exc}")
            self.accounts_changed.emit()
            self.finished_summary.emit(success, total_jobs, total, stopped)
