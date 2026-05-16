import PySide6.QtCore
import sys, random, os
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEnginePage, QWebEngineCookieStore, QWebEngineProfile, QWebEngineSettings, QWebEngineUrlRequestInterceptor
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QTabWidget, QHBoxLayout, QFileDialog, QPushButton, QMainWindow, QLineEdit, QStatusBar, QToolBar, QVBoxLayout, QWidget

class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.blocklist = set()
        self.loadList()
    
    def loadList(self):
        with open("blocklist.txt") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2:
                        self.blocklist.add(parts[1])
    
    def interceptRequest(self, info):
        host = info.requestUrl().host()
        if any(host.endswith(domain) for domain in self.blocklist):
            info.block(True)

class LyraBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        if not os.path.exists(os.path.expanduser("~/.local/share/LyraBrowser")):
            os.mkdir(os.path.expanduser("~/.local/share/LyraBrowser"))
        self.setMinimumSize(600, 600)
        self.setWindowTitle("Lyra Browser")
        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.tabs = QTabWidget()
        self.urlBar = QLineEdit()
        self.urlBar.setPlaceholderText("Enter URL")
        self.urlBar.setText("https://www.google.com")
        self.goButton = QPushButton("Go")
        self.goButton.clicked.connect(self.go)
        self.backButton = QPushButton("Back")
        self.forwardButton = QPushButton("Forward")
        self.backButton.clicked.connect(lambda: self.tabs.currentWidget().back())
        self.forwardButton.clicked.connect(lambda: self.tabs.currentWidget().forward())
        layout.addWidget(self.tabs)
        self.addTabBtn = QPushButton("+")
        self.addTabBtn.clicked.connect(self.addTabs)
        self.tabs.setCornerWidget(self.addTabBtn)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.currentChanged.connect(self.urlChange)
        self.tabs.tabCloseRequested.connect(self.removeTab)
        self.refreshButton = QPushButton("Refresh")
        self.refreshButton.clicked.connect(lambda: self.tabs.currentWidget().reload())
        self.profile = QWebEngineProfile("User", self)
        store = self.profile.cookieStore()
        self.adblocker = AdBlockInterceptor()
        self.profile.setUrlRequestInterceptor(self.adblocker)
        self.profile.setPersistentStoragePath(os.path.expanduser("~/.local/share/LyraBrowser"))
        self.profile.downloadRequested.connect(self.download)
        print(self.profile.persistentStoragePath())
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        store.setCookieFilter(self.cookieFilter)
        self.tabs.setDocumentMode(True)
        layout.setContentsMargins(0,10,0,10)
        topBarLayout = QHBoxLayout()
        topBarLayout.addWidget(self.backButton)
        topBarLayout.addWidget(self.forwardButton)
        topBarLayout.addWidget(self.refreshButton)
        topBarLayout.addWidget(self.urlBar)
        topBarLayout.addWidget(self.goButton)
        layout.addLayout(topBarLayout)
        self.addTabs()
    def go(self):
        url = self.urlBar.text()
        if not self.urlBar.text().startswith("https://"):
            url = "https://" + url
        self.tabs.currentWidget().setUrl(QUrl(url))
    def interceptRequest(self, info):
        if info.firstPartyUrl().host() != info.requestUrl().host():
            if not any(w in info.requestUrl().host() for w in WHITELIST):
                info.block(True)
    def cookieFilter(self, info):
        allowed = info.origin.host() == info.firstPartyUrl.host() or info.firstPartyUrl.host() == ""
        if not allowed:
            pass
        return allowed

    def addTabs(self):
        self.view = QWebEngineView()
        page = QWebEnginePage(self.profile, self.view)
        self.view.setPage(page)
        self.view.setUrl(QUrl("https://www.google.com"))
        self.tabs.addTab(self.view, "Google")
        self.tabs.setCurrentWidget(self.view)
        self.view.urlChanged.connect(self.urlChange)
        self.view.titleChanged.connect(self.titlechange)
        self.view.iconChanged.connect(lambda icon, v=self.view: self.tabs.setTabIcon(self.tabs.indexOf(v), icon))
        self.view.loadFinished.connect(lambda _, v=self.view: v.page().runJavaScript("""
        const style = document.createElement('style');
        style.textContent = '.ad, .ads, .advertisement, #ad, #ads, [class*="banner"], [id*="banner"], [class*="sponsor"] { display: none !important; }';
        document.head.appendChild(style);
        window.adsbygoogle = { loaded: true };
        window.googletag = { cmd: [], pubads: () => ({}) };
    """))

    def removeTab(self, index):
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.close()
    def urlChange(self, url=None):
        current = self.tabs.currentWidget()
        if current:
            self.currentUrl = current.url()
            self.urlBar.setText(self.currentUrl.toString())
    def titlechange(self, title):
        print(len(title))
        if len(title) > 20:
            print("titile setting")
            self.shortenedTitle = title[:17] + "..."
            self.tabs.setTabText(self.tabs.indexOf(self.view), self.shortenedTitle)
        else:
            self.tabs.setTabText(self.tabs.indexOf(self.view), self.tabs.currentWidget().page().title())
    def download(self, download):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", download.suggestedFileName())
        if path:
            download.setDownloadFileName(path)
            download.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LyraBrowser()
    window.show()
    sys.exit(app.exec())