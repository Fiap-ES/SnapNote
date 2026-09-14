from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.toast import toast

import library
import storage
from core.index import DuplicateKeywordError, Keyword
from ui import dialogs
from ui.widgets import RowCard, SnapScreen

Builder.load_string("""
#:import theme ui.theme

<KeywordItem>:
    on_release: root.dispatch("on_edit_requested")
    IconGlyph:
        icon: "tag-outline"
        font_size: sp(theme.CARD_ICON_SIZE)
        color: theme.ACCENT
    Label:
        text: root.keyword.term
        font_name: theme.FONT_REGULAR
        font_size: sp(theme.FONT_BODY)
        color: theme.TEXT
        halign: "left"
        valign: "center"
        text_size: self.size
        shorten: True
    ToolIcon:
        icon: "delete-outline"
        pos_hint: {"center_y": .5}
        on_release: root.dispatch("on_remove_requested")

<KeywordsScreen>:
    md_bg_color: theme.LAYER_0
    MDBoxLayout:
        orientation: "vertical"
        ScreenBar:
            title: "Palavras-chave"
            on_back: root.dispatch("on_back")
            ToolIcon:
                icon: "plus"
                pos_hint: {"center_y": .5}
                on_release: root.prompt_new()
        MDLabel:
            text: root.message
            font_name: theme.FONT
            halign: "center"
            theme_text_color: "Custom"
            text_color: theme.TEXT_MUTED
            size_hint_y: None
            height: dp(theme.MESSAGE_HEIGHT) if self.text else 0
        MDScrollView:
            MDBoxLayout:
                id: keyword_list
                orientation: "vertical"
                adaptive_height: True
                padding: dp(theme.PADDING), dp(theme.SPACING), dp(theme.PADDING), dp(theme.PADDING)
                spacing: dp(theme.SPACING)
""")

DUPLICATE_MESSAGE = "Já existe uma palavra-chave equivalente."


class KeywordItem(ButtonBehavior, RowCard):
    __events__ = ("on_edit_requested", "on_remove_requested")
    keyword = ObjectProperty(None)

    def on_edit_requested(self) -> None:
        pass

    def on_remove_requested(self) -> None:
        pass


class KeywordsScreen(SnapScreen):
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
