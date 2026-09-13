from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivymd.toast import toast
from kivymd.uix.list import IconLeftWidget, IconRightWidget, OneLineAvatarIconListItem
from kivymd.uix.screen import MDScreen

import library
import storage
from core.index import DuplicateKeywordError, Keyword
from ui import dialogs

Builder.load_string("""
<KeywordItem>:
    text: root.keyword.term
    on_release: root.dispatch("on_edit_requested")
    IconLeftWidget:
        icon: "tag"
    IconRightWidget:
        icon: "delete"
        on_release: root.dispatch("on_remove_requested")

<KeywordsScreen>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Palavras-chave"
            left_action_items: [["arrow-left", lambda _button: root.dispatch("on_back")]]
            right_action_items: [["plus", lambda _button: root.prompt_new()]]
        MDLabel:
            text: root.message
            halign: "center"
            theme_text_color: "Hint"
            size_hint_y: None
            height: dp(56) if self.text else 0
        MDScrollView:
            MDList:
                id: keyword_list
""")

DUPLICATE_MESSAGE = "Já existe uma palavra-chave equivalente."


class KeywordItem(OneLineAvatarIconListItem):
    __events__ = ("on_edit_requested", "on_remove_requested")
    keyword = ObjectProperty(None)

    def on_edit_requested(self) -> None:
        pass

    def on_remove_requested(self) -> None:
        pass


class KeywordsScreen(MDScreen):
    __events__ = ("on_back",)
    message = StringProperty("")

    def refresh(self) -> None:
        keywords = library.keywords(storage.index_path())
        self.message = "" if keywords else "Nenhuma palavra-chave cadastrada."
        self.ids.keyword_list.clear_widgets()
        for keyword in keywords:
            item = KeywordItem(keyword=keyword)
            item.bind(on_edit_requested=self._prompt_rename, on_remove_requested=self._confirm_remove)
            self.ids.keyword_list.add_widget(item)

    def prompt_new(self) -> None:
        dialogs.prompt("Nova palavra-chave", "", "Adicionar", self.add)

    def add(self, term: str) -> None:
        try:
            library.add_keyword(storage.index_path(), term)
        except DuplicateKeywordError:
            toast(DUPLICATE_MESSAGE)
        self.refresh()

    def rename(self, keyword: Keyword, term: str) -> None:
        try:
            library.rename_keyword(storage.index_path(), keyword.id, term)
        except DuplicateKeywordError:
            toast(DUPLICATE_MESSAGE)
        self.refresh()

    def remove(self, keyword: Keyword) -> None:
        library.remove_keyword(storage.index_path(), keyword.id)
        self.refresh()

    def on_back(self) -> None:
        pass

    def _prompt_rename(self, item: KeywordItem) -> None:
        dialogs.prompt(
            "Editar palavra-chave",
            item.keyword.term,
            "Salvar",
            lambda term: self.rename(item.keyword, term),
        )

    def _confirm_remove(self, item: KeywordItem) -> None:
        dialogs.confirm(
            f'Remover a palavra-chave "{item.keyword.term}"?',
            "Remover",
            lambda: self.remove(item.keyword),
        )
