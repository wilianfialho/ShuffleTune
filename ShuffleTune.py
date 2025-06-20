import os
import random
import sys
import threading
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window

# CORREÇÃO: Importação compatível com múltiplas versões do Kivy.
# Tenta importar 'dp' do novo local (Kivy >= 2.0) e, se falhar,
# importa do local antigo (Kivy < 2.0).
try:
    from kivy.utils import dp
except ImportError:
    from kivy.metrics import dp

# KV Language String: Define toda a interface do usuário.
KV_STRING = """
#:import sys sys

# CORREÇÃO: A importação de 'dp' foi removida daqui e agora é
# tratada no lado do Python para garantir a compatibilidade.
# O Kivy encontrará 'dp' no escopo do Python automaticamente.

# Definindo estilos para os widgets customizados.
<GlassButton@Button>:
    background_normal: ''
    background_color: [0.2, 0.6, 0.8, 0.7] # Azul semi-transparente
    color: [1, 1, 1, 1]
    font_size: 16
    size_hint_y: None
    height: dp(40)
    canvas.before:
        Color:
            rgba: self.background_color
        RoundedRectangle:
            size: self.size
            pos: self.pos
            radius: [dp(10)]

<AccentButton@GlassButton>:
    background_color: [0.08, 0.63, 0.52, 0.8] # Verde-azulado

<WarningButton@GlassButton>:
    background_color: [0.9, 0.3, 0.2, 0.8] # Vermelho de aviso

<ShuffleButton@GlassButton>:
    background_color: [0.96, 0.61, 0.07, 0.8] # Laranja

<RenameButton@GlassButton>:
    background_color: [0.18, 0.8, 0.44, 0.8] # Verde

<DarkTextInput@TextInput>:
    background_color: [0.2, 0.3, 0.4, 0.9]
    foreground_color: [1, 1, 1, 1]
    font_size: 16
    padding: [dp(10), dp(10), dp(10), dp(10)]
    multiline: False
    size_hint_y: None
    height: dp(40)
    cursor_color: [0.08, 0.63, 0.52, 1]
    border: [dp(8), dp(8), dp(8), dp(8)]

<DarkLabel@Label>:
    color: [1, 1, 1, 1]
    font_size: 14
    halign: 'left'
    valign: 'middle'
    size_hint_y: None
    height: dp(30)
    text_size: self.width, None

<DarkCheckBox@CheckBox>:
    color: [1, 1, 1, 1]
    size_hint: None, None
    width: dp(30)
    height: dp(30)

<DarkProgressBar@ProgressBar>:
    size_hint_y: None
    height: dp(25)
    canvas:
        Color:
            rgba: [0.2, 0.3, 0.4, 0.7]
        RoundedRectangle:
            size: self.size
            pos: self.pos
            radius: [dp(5)]
        Color:
            rgba: [0.08, 0.63, 0.52, 0.9] # Verde-azulado para o progresso
        RoundedRectangle:
            size: self.size[0] * self.value / self.max if self.max > 0 else 0, self.size[1]
            pos: self.pos
            radius: [dp(5)]

# MELHORIA: Widget para itens da lista de arquivos no RecycleView.
<FileListItem>:
    halign: 'left'
    valign: 'top'
    text_size: self.width, None
    size_hint_y: None
    height: self.texture_size[1] + dp(10) # Ajusta a altura baseada no conteúdo

# Layout Principal
BoxLayout:
    orientation: 'horizontal'
    padding: dp(10)
    spacing: dp(10)

    # Painel Esquerdo (Controles)
    BoxLayout:
        id: left_panel
        orientation: 'vertical'
        size_hint: 0.6, 1
        spacing: dp(10)

        DarkLabel:
            text: app.ui_source_folder_label
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(5)
            DarkTextInput:
                id: txt_folder
                text: app.folder_path
                hint_text: app.ui_folder_hint
                on_text: app.folder_path = self.text
            GlassButton:
                text: app.ui_browse_button
                on_release: app.browse_folder('input')

        DarkLabel:
            text: app.ui_output_folder_label
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(5)
            DarkTextInput:
                id: txt_output_folder
                text: app.output_folder_path
                hint_text: app.ui_output_folder_hint
                on_text: app.output_folder_path = self.text
            GlassButton:
                text: app.ui_browse_button
                on_release: app.browse_folder('output')

        GridLayout:
            cols: 2
            size_hint_y: None
            height: dp(120)
            spacing: dp(5)
            DarkCheckBox:
                id: chk_include_subfolders
                active: app.include_subfolders_active
                on_active: app.include_subfolders_active = self.active
            DarkLabel:
                text: app.ui_include_subfolders_label
            DarkCheckBox:
                id: chk_open_output_folder
                active: app.open_output_folder_after_rename
                on_active: app.open_output_folder_after_rename = self.active
            DarkLabel:
                text: app.ui_open_folder_label
            DarkCheckBox:
                id: chk_sanitize_names
                active: app.sanitize_names_active
                on_active: app.sanitize_names_active = self.active
            DarkLabel:
                text: app.ui_sanitize_names_label

        Widget:
            size_hint_y: None
            height: dp(15)

        DarkLabel:
            text: app.ui_extensions_label
        DarkTextInput:
            id: txt_extensions
            text: app.supported_extensions_text
            on_text: app.on_extensions_text_changed(self.text)
        
        DarkLabel:
            text: app.ui_format_label
        DarkTextInput:
            id: txt_format
            text: "{index} - {name}"
            on_text: app.update_preview()
            disabled: chk_add_prefix.active
        
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(5)
            DarkCheckBox:
                id: chk_add_prefix
                active: True
                on_active: app.update_preview()
            DarkLabel:
                text: app.ui_add_prefix_label

        Widget:
            size_hint_y: None
            height: dp(15)

        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            ShuffleButton:
                id: btn_shuffle
                text: app.ui_shuffle_button
                on_release: app.shuffle_files()
            RenameButton:
                id: btn_rename
                text: app.ui_rename_button
                on_release: app.confirm_rename()
            WarningButton:
                id: btn_cancel
                text: app.ui_cancel_button
                on_release: app.cancel_operation()
                disabled: True
            GlassButton:
                id: btn_clear_reset
                text: app.ui_clear_button
                on_release: app.clear_reset_app()
        
        Widget:
            size_hint_y: None
            height: dp(15)

        DarkProgressBar:
            id: progress_bar
            max: app.progress_max
            value: app.progress_value
        DarkLabel:
            id: lbl_status
            text: app.status_text

        # Espaçador para empurrar botões para baixo
        Widget: 

        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(10)
            AccentButton:
                id: btn_lang_pt
                text: "Português"
                on_release: app.set_language("pt")
                background_color: [0.08, 0.63, 0.52, 0.8] if app.language == 'pt' else [0.2, 0.6, 0.8, 0.7]
            GlassButton:
                id: btn_lang_en
                text: "English"
                on_release: app.set_language("en")
                background_color: [0.08, 0.63, 0.52, 0.8] if app.language == 'en' else [0.2, 0.6, 0.8, 0.7]
            GlassButton:
                text: app.ui_help_button
                on_release: app.show_help_popup()
            GlassButton:
                text: app.ui_about_button
                on_release: app.show_about_popup()

    # Painel Direito (Lista de Arquivos e Pré-visualização)
    BoxLayout:
        orientation: 'vertical'
        size_hint: 0.4, 1
        padding: dp(10)
        spacing: dp(10)

        DarkLabel:
            text: app.ui_files_found_label
        DarkTextInput:
            id: txt_search_files
            hint_text: app.ui_search_hint
            on_text: app.on_search_text_changed(self.text)
        
        RecycleView:
            id: file_list_rv
            viewclass: 'FileListItem'
            data: app.recycle_view_data
            RecycleBoxLayout:
                default_size: None, dp(30)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
                spacing: dp(2)
        
        DarkLabel:
            text: app.ui_rename_preview_label
        DarkLabel:
            id: lbl_preview
            text: app.preview_text
"""

# Classe para o item da lista de arquivos do RecycleView
class FileListItem(Label):
    pass

# Worker para renomear arquivos em uma thread separada
class RenameWorker(threading.Thread):
    def __init__(self, files, folder, pattern, add_number_prefix, app_instance, output_folder=None, sanitize_names=False):
        super().__init__()
        self.files = files
        self.folder = folder
        self.pattern = pattern
        self.add_number_prefix = add_number_prefix
        self.app_instance = app_instance
        self.output_folder = output_folder if output_folder else folder
        self.sanitize_names = sanitize_names
        self._is_running = True

    def _sanitize_filename(self, filename):
        if not self.sanitize_names:
            return filename
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        filename = ' '.join(filename.split())
        return filename.strip()

    def run(self):
        try:
            total_files = len(self.files)
            for i, file_relative_path in enumerate(self.files):
                if not self._is_running:
                    break

                original_full_path = os.path.join(self.folder, file_relative_path)
                file_name_only = os.path.basename(file_relative_path)

                index = str(i + 1).zfill(len(str(total_files)))
                name, ext = os.path.splitext(file_name_only)
                
                name = self._sanitize_filename(name)

                if self.add_number_prefix:
                    new_name_base = f"{index} - {name}"
                else:
                    new_name_base = self.pattern.replace("{index}", index).replace("{name}", name)
                
                new_name_with_ext = new_name_base + ext
                relative_dir = os.path.dirname(file_relative_path)
                
                output_dir = os.path.join(self.output_folder, relative_dir)
                os.makedirs(output_dir, exist_ok=True)

                new_full_path = os.path.join(output_dir, new_name_with_ext)

                counter = 1
                while os.path.exists(new_full_path) and original_full_path.lower() != new_full_path.lower():
                    new_name_collision = f"{new_name_base} ({counter}){ext}"
                    new_full_path = os.path.join(output_dir, new_name_collision)
                    counter += 1
                
                if original_full_path.lower() != new_full_path.lower():
                    os.rename(original_full_path, new_full_path)
                
                Clock.schedule_once(lambda dt, cur=i + 1, n_name=os.path.basename(new_full_path):
                                    self.app_instance.on_rename_progress(cur, n_name))

            final_message = "Operação concluída com sucesso" if self._is_running else "Operação cancelada"
            Clock.schedule_once(lambda dt, success=self._is_running, msg=final_message:
                                self.app_instance.on_rename_finished(success, msg))
        except Exception as e:
            Clock.schedule_once(lambda dt, msg=f"Erro: {str(e)}":
                                self.app_instance.on_rename_finished(False, msg))

    def stop(self):
        self._is_running = False

# Classe principal da Aplicação
class ShuffleTuneApp(App):
    # --- Propriedades de Estado ---
    language = StringProperty("pt")
    folder_path = StringProperty("")
    output_folder_path = StringProperty("")
    status_text = StringProperty("")
    preview_text = StringProperty("")
    mp3_files = ListProperty([])
    filtered_files = ListProperty([])
    progress_value = NumericProperty(0)
    progress_max = NumericProperty(100)
    include_subfolders_active = BooleanProperty(False)
    open_output_folder_after_rename = BooleanProperty(False)
    sanitize_names_active = BooleanProperty(False)
    supported_extensions_text = StringProperty("mp3, wav, flac, ogg, m4a")
    supported_extensions = ListProperty(['.mp3', '.wav', '.flac', '.ogg', '.m4a'])
    rename_worker = None
    
    # --- Propriedades de UI para Internacionalização ---
    ui_source_folder_label = StringProperty()
    ui_output_folder_label = StringProperty()
    ui_folder_hint = StringProperty()
    ui_output_folder_hint = StringProperty()
    ui_browse_button = StringProperty()
    ui_include_subfolders_label = StringProperty()
    ui_open_folder_label = StringProperty()
    ui_sanitize_names_label = StringProperty()
    ui_extensions_label = StringProperty()
    ui_format_label = StringProperty()
    ui_add_prefix_label = StringProperty()
    ui_shuffle_button = StringProperty()
    ui_rename_button = StringProperty()
    ui_cancel_button = StringProperty()
    ui_clear_button = StringProperty()
    ui_help_button = StringProperty()
    ui_about_button = StringProperty()
    ui_files_found_label = StringProperty()
    ui_search_hint = StringProperty()
    ui_rename_preview_label = StringProperty()
    ui_yes_button = StringProperty()
    ui_no_button = StringProperty()
    ui_select_button = StringProperty()
    ui_ready_status = StringProperty()
    ui_files_found_status = StringProperty()
    ui_no_files_found = StringProperty()
    ui_and_more_files_status = StringProperty()
    ui_original_to_new_name = StringProperty()
    ui_no_files_to_shuffle = StringProperty()
    ui_shuffled_successfully = StringProperty()
    ui_select_folder_first = StringProperty()
    ui_no_files_to_rename = StringProperty()
    ui_pattern_error = StringProperty()
    ui_confirm_rename_title = StringProperty()
    ui_confirm_rename_message = StringProperty()
    ui_select_folder_title = StringProperty()
    ui_starting_rename = StringProperty()
    ui_renaming_status = StringProperty()
    ui_op_completed = StringProperty()
    ui_op_failed = StringProperty()
    ui_dest_folder_not_found = StringProperty()
    ui_cancelling_op = StringProperty()
    
    # --- Propriedade de Dados para RecycleView ---
    recycle_view_data = ListProperty()

    def build(self):
        Window.clearcolor = (0.17, 0.24, 0.31, 1)
        return Builder.load_string(KV_STRING)

    def on_start(self):
        self.set_language(self.language)
        self.bind(folder_path=self.on_folder_or_subfolder_changed,
                  include_subfolders_active=self.on_folder_or_subfolder_changed)
        self.update_preview()
        
    def on_folder_or_subfolder_changed(self, *args):
        folder = self.folder_path
        if not (folder and os.path.isdir(folder)):
            self.mp3_files = []
            self.filtered_files = []
            if hasattr(self, 'ui_ready_status'): # Garante que a UI foi inicializada
                self.status_text = self.ui_ready_status
                self.update_file_list_display()
                self.update_preview()
            return

        temp_files = []
        try:
            if self.include_subfolders_active:
                for root, _, files in os.walk(folder):
                    for f in files:
                        if os.path.splitext(f)[1].lower() in self.supported_extensions:
                            temp_files.append(os.path.relpath(os.path.join(root, f), folder))
            else:
                for f in os.listdir(folder):
                    full_path = os.path.join(folder, f)
                    if os.path.isfile(full_path) and os.path.splitext(f)[1].lower() in self.supported_extensions:
                        temp_files.append(f)
            
            self.mp3_files = sorted(temp_files)
            self.on_search_text_changed(self.root.ids.txt_search_files.text if self.root else "")
            self.status_text = self.ui_files_found_status.format(count=len(self.mp3_files))
            self.update_preview()
        except OSError as e:
            self.show_message("Erro de Permissão", f"Não foi possível acessar a pasta:\n{e}", 'error')
            self.mp3_files = []
            self.filtered_files = []

    def on_extensions_text_changed(self, value):
        ext_list = [f".{ext.strip().lower()}" for ext in value.split(',') if ext.strip()]
        self.supported_extensions = ext_list if ext_list else ['.mp3']
        self.on_folder_or_subfolder_changed()

    def on_search_text_changed(self, value):
        search_term = value.lower()
        if search_term:
            self.filtered_files = [f for f in self.mp3_files if search_term in os.path.basename(f).lower()]
        else:
            self.filtered_files = list(self.mp3_files)
        self.update_file_list_display()

    def update_file_list_display(self):
        if not self.filtered_files:
            self.recycle_view_data = [{'text': self.ui_no_files_found}]
        else:
            display_limit = 100
            self.recycle_view_data = [{'text': os.path.basename(f)} for f in self.filtered_files[:display_limit]]
            if len(self.filtered_files) > display_limit:
                 self.recycle_view_data.append({'text': f"\n... {self.ui_and_more_files_status}"})

    def update_preview(self, *args):
        if not self.root: return
        if not self.filtered_files:
            self.preview_text = self.ui_original_to_new_name
            return

        sample_file_name_only = os.path.basename(self.filtered_files[0])
        name, ext = os.path.splitext(sample_file_name_only)
        
        if self.sanitize_names_active:
            name = self._sanitize_filename_preview(name)

        if self.root.ids.chk_add_prefix.active:
            new_name = f"001 - {name}{ext}"
        else:
            pattern = self.root.ids.txt_format.text
            new_name = pattern.replace("{index}", "001").replace("{name}", name) + ext

        self.preview_text = f"{sample_file_name_only} -> {new_name}"

    def _sanitize_filename_preview(self, filename):
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return ' '.join(filename.split()).strip()

    def browse_folder(self, folder_type):
        if sys.platform == 'android':
            self.show_message("Função Indisponível", "O seletor de pastas não é suportado em Android.", 'error')
            return

        initial_path = os.path.expanduser('~')
        if folder_type == 'input' and self.folder_path and os.path.isdir(self.folder_path):
            initial_path = self.folder_path
        
        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserListView(path=initial_path, dirselect=True)
        content.add_widget(file_chooser)
        
        btn_layout = BoxLayout(size_hint_y=None, height=dp(44))
        btn_select = Button(text=self.ui_select_button)
        btn_cancel = Button(text=self.ui_cancel_button)
        btn_layout.add_widget(btn_select)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        popup = Popup(title=self.ui_select_folder_title, content=content, size_hint=(0.9, 0.9))
        
        def select_path(instance):
            if file_chooser.selection:
                selected_dir = file_chooser.selection[0]
                if folder_type == 'input':
                    self.folder_path = selected_dir
                else:
                    self.output_folder_path = selected_dir
            popup.dismiss()
        
        btn_select.bind(on_release=select_path)
        btn_cancel.bind(on_release=popup.dismiss)
        popup.open()
        
    def shuffle_files(self, *args):
        if not self.mp3_files:
            self.show_message("Erro", self.ui_no_files_to_shuffle, 'error')
            return
        random.shuffle(self.mp3_files)
        self.on_search_text_changed(self.root.ids.txt_search_files.text)
        self.update_preview()
        self.show_message("Sucesso", self.ui_shuffled_successfully, 'info')

    def confirm_rename(self, *args):
        if not self.folder_path or not os.path.isdir(self.folder_path):
            self.show_message("Erro", self.ui_select_folder_first, 'error')
            return
        if not self.mp3_files:
            self.show_message("Erro", self.ui_no_files_to_rename, 'error')
            return
        if not self.root.ids.chk_add_prefix.active:
            pattern = self.root.ids.txt_format.text
            if "{index}" not in pattern and "{name}" not in pattern:
                self.show_message("Erro", self.ui_pattern_error, 'error')
                return

        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=self.ui_confirm_rename_message, text_size=(Window.width * 0.7, None), halign='center'))
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(40))
        btn_yes = Button(text=self.ui_yes_button)
        btn_no = Button(text=self.ui_no_button)
        btn_layout.add_widget(btn_yes)
        btn_layout.add_widget(btn_no)
        content.add_widget(btn_layout)
        popup = Popup(title=self.ui_confirm_rename_title, content=content, size_hint=(0.8, 0.5), auto_dismiss=False)
        btn_yes.bind(on_release=lambda x: self._proceed_with_rename(popup))
        btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def _proceed_with_rename(self, popup_instance):
        popup_instance.dismiss()
        self.toggle_ui_elements(True)
        self.progress_max = len(self.mp3_files)
        self.progress_value = 0
        self.status_text = self.ui_starting_rename
        self.rename_worker = RenameWorker(
            self.mp3_files, self.folder_path, self.root.ids.txt_format.text,
            self.root.ids.chk_add_prefix.active, self,
            output_folder=self.output_folder_path if self.output_folder_path else None,
            sanitize_names=self.sanitize_names_active)
        self.rename_worker.start()

    def on_rename_progress(self, current, new_name):
        self.progress_value = current
        self.status_text = self.ui_renaming_status.format(new_name=new_name, current=current, total=self.progress_max)
        
    def on_rename_finished(self, success, message):
        self.toggle_ui_elements(False)
        if success:
            self.status_text = self.ui_op_completed
            self.show_message("Sucesso", message, 'info')
            if self.open_output_folder_after_rename:
                self.open_folder_in_explorer(self.output_folder_path if self.output_folder_path else self.folder_path)
        else:
            self.status_text = self.ui_op_failed
            self.show_message("Erro", message, 'error')
        self.on_folder_or_subfolder_changed()

    def open_folder_in_explorer(self, path):
        if not os.path.isdir(path):
            self.show_message("Erro", self.ui_dest_folder_not_found, 'error')
            return
        try:
            if sys.platform == "win32":
                os.startfile(os.path.realpath(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.show_message("Erro", f"Não foi possível abrir a pasta:\n{e}", 'error')

    def cancel_operation(self, *args):
        if self.rename_worker and self.rename_worker.is_alive():
            self.rename_worker.stop()
            self.status_text = self.ui_cancelling_op

    def clear_reset_app(self, *args):
        self.folder_path = ""
        self.output_folder_path = ""
        self.root.ids.txt_format.text = "{index} - {name}"
        self.root.ids.chk_add_prefix.active = True
        self.include_subfolders_active = False
        self.open_output_folder_after_rename = False
        self.sanitize_names_active = False
        self.supported_extensions_text = "mp3, wav, flac, ogg, m4a"
        self.root.ids.txt_search_files.text = ""
        self.progress_value = 0
        self.on_folder_or_subfolder_changed()

    def toggle_ui_elements(self, is_running):
        for widget_id in self.root.ids:
            if widget_id not in ['btn_cancel', 'progress_bar', 'lbl_status', 'file_list_rv']:
                self.root.ids[widget_id].disabled = is_running
        self.root.ids.btn_cancel.disabled = not is_running

    def set_language(self, lang):
        self.language = lang
        if lang == "pt":
            self.title = "ShuffleTune - Renomeador de Arquivos"
            self.ui_source_folder_label = "Pasta de Origem:"
            self.ui_output_folder_label = "Pasta de Destino (opcional):"
            self.ui_folder_hint = "Selecione a pasta com os arquivos"
            self.ui_output_folder_hint = "Deixe em branco para usar a pasta de origem"
            self.ui_browse_button = "Procurar"
            self.ui_include_subfolders_label = "Incluir Subpastas"
            self.ui_open_folder_label = "Abrir pasta de destino ao concluir"
            self.ui_sanitize_names_label = "Limpar nomes (remover caracteres inválidos)"
            self.ui_extensions_label = "Extensões (separadas por vírgula):"
            self.ui_format_label = "Formato da Renomeação:"
            self.ui_add_prefix_label = "Adicionar prefixo numérico sequencial"
            self.ui_shuffle_button = "Embaralhar"
            self.ui_rename_button = "Renomear"
            self.ui_cancel_button = "Cancelar"
            self.ui_clear_button = "Limpar"
            self.ui_help_button = "Ajuda"
            self.ui_about_button = "Sobre"
            self.ui_files_found_label = "Arquivos Encontrados:"
            self.ui_search_hint = "Buscar arquivos..."
            self.ui_rename_preview_label = "Pré-visualização:"
            self.ui_yes_button = "Sim"
            self.ui_no_button = "Não"
            self.ui_select_button = "Selecionar"
            self.ui_ready_status = "Pronto"
            # CORREÇÃO: Removido um par de chaves extra.
            self.ui_files_found_status = "{count} arquivos encontrados"
            self.ui_no_files_found = "Nenhum arquivo encontrado ou filtrado."
            self.ui_and_more_files_status = "e mais..."
            self.ui_original_to_new_name = "Original -> Novo Nome"
            self.ui_no_files_to_shuffle = "Nenhum arquivo encontrado para embaralhar."
            self.ui_shuffled_successfully = "Arquivos embaralhados com sucesso!"
            self.ui_select_folder_first = "Por favor, selecione uma pasta de origem primeiro."
            self.ui_no_files_to_rename = "Nenhum arquivo encontrado para renomear."
            self.ui_pattern_error = "O padrão deve conter '{index}' ou '{name}'."
            self.ui_confirm_rename_title = "Confirmar Renomeação"
            self.ui_confirm_rename_message = "Tem certeza?\\nEsta operação modifica os arquivos permanentemente."
            self.ui_select_folder_title = "Selecionar Pasta"
            self.ui_starting_rename = "Iniciando renomeação..."
            self.ui_renaming_status = "Renomeando: {new_name} ({current}/{total})"
            self.ui_op_completed = "Operação concluída com sucesso."
            self.ui_op_failed = "Operação falhou ou foi cancelada."
            self.ui_dest_folder_not_found = "Pasta de destino não encontrada."
            self.ui_cancelling_op = "Cancelando operação..."
        else: # English
            self.title = "ShuffleTune - File Renamer"
            self.ui_source_folder_label = "Source Folder:"
            self.ui_output_folder_label = "Output Folder (optional):"
            self.ui_folder_hint = "Select the folder with your files"
            self.ui_output_folder_hint = "Leave blank to use the source folder"
            self.ui_browse_button = "Browse"
            self.ui_include_subfolders_label = "Include Subfolders"
            self.ui_open_folder_label = "Open output folder when done"
            self.ui_sanitize_names_label = "Sanitize names (remove invalid chars)"
            self.ui_extensions_label = "Extensions (comma-separated):"
            self.ui_format_label = "Renaming Pattern:"
            self.ui_add_prefix_label = "Add sequential number prefix"
            self.ui_shuffle_button = "Shuffle"
            self.ui_rename_button = "Rename"
            self.ui_cancel_button = "Cancel"
            self.ui_clear_button = "Clear"
            self.ui_help_button = "Help"
            self.ui_about_button = "About"
            self.ui_files_found_label = "Files Found:"
            self.ui_search_hint = "Search files..."
            self.ui_rename_preview_label = "Preview:"
            self.ui_yes_button = "Yes"
            self.ui_no_button = "No"
            self.ui_select_button = "Select"
            self.ui_ready_status = "Ready"
            self.ui_files_found_status = "Found {count} files"
            self.ui_no_files_found = "No files found or filtered."
            self.ui_and_more_files_status = "and more..."
            self.ui_original_to_new_name = "Original -> New Name"
            self.ui_no_files_to_shuffle = "No files found to shuffle."
            self.ui_shuffled_successfully = "Files shuffled successfully!"
            self.ui_select_folder_first = "Please select a source folder first."
            self.ui_no_files_to_rename = "No files found to rename."
            self.ui_pattern_error = "Pattern must contain '{index}' or '{name}'."
            self.ui_confirm_rename_title = "Confirm Rename"
            self.ui_confirm_rename_message = "Are you sure?\\nThis operation permanently modifies your files."
            self.ui_select_folder_title = "Select Folder"
            self.ui_starting_rename = "Starting renaming..."
            self.ui_renaming_status = "Renaming: {new_name} ({current}/{total})"
            self.ui_op_completed = "Operation completed successfully."
            self.ui_op_failed = "Operation failed or was cancelled."
            self.ui_dest_folder_not_found = "Destination folder not found."
            self.ui_cancelling_op = "Cancelling operation..."
        
        self.on_folder_or_subfolder_changed()

    def show_message(self, title, message, msg_type):
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=message, text_size=(Window.width * 0.7, None), halign='center', valign='middle'))
        close_button = Button(text="OK", size_hint_y=None, height=dp(44))
        content.add_widget(close_button)

        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        close_button.bind(on_release=popup.dismiss)
        popup.open()

    def show_help_popup(self, *args):
        help_text_pt = (
            "1. [b]Pasta de Origem:[/b] Selecione a pasta com seus arquivos.\\n"
            "2. [b]Pasta de Destino:[/b] (Opcional) Escolha uma pasta para salvar os arquivos renomeados. Se em branco, os arquivos são modificados na origem.\\n"
            "3. [b]Incluir Subpastas:[/b] Processa arquivos em todas as subpastas.\\n"
            "4. [b]Abrir Pasta de Destino:[/b] Abre a pasta de destino no final.\\n"
            "5. [b]Limpar Nomes:[/b] Remove caracteres inválidos como / ? * < > dos nomes.\\n"
            "6. [b]Extensões:[/b] Defina os tipos de arquivo a processar (ex: mp3, wav).\\n"
            "7. [b]Formato:[/b] Use {index} para número e {name} para o nome original.\\n"
            "8. [b]Embaralhar:[/b] Aleatoriza a ordem dos arquivos antes de renomear.\\n"
            "9. [b]Renomear:[/b] Inicia a operação."
        )
        help_text_en = (
            "1. [b]Source Folder:[/b] Select the folder with your files.\\n"
            "2. [b]Output Folder:[/b] (Optional) Choose a folder to save the renamed files. If blank, files are modified in place.\\n"
            "3. [b]Include Subfolders:[/b] Process files in all subfolders.\\n"
            "4. [b]Open Output Folder:[/b] Opens the destination folder when complete.\\n"
            "5. [b]Sanitize Names:[/b] Removes invalid characters like / ? * < > from names.\\n"
            "6. [b]Extensions:[/b] Define file types to process (e.g., mp3, wav).\\n"
            "7. [b]Pattern:[/b] Use {index} for a number and {name} for the original name.\\n"
            "8. [b]Shuffle:[/b] Randomizes the file order before renaming.\\n"
            "9. [b]Rename:[/b] Starts the operation."
        )
        
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        scroll_view = ScrollView()
        help_label = Label(
            text=help_text_pt if self.language == 'pt' else help_text_en,
            text_size=(Window.width * 0.75, None),
            halign='left', valign='top',
            markup=True
        )
        help_label.bind(texture_size=help_label.setter('size'))
        scroll_view.add_widget(help_label)
        content.add_widget(scroll_view)
        
        close_button = Button(text="OK", size_hint_y=None, height=dp(44))
        content.add_widget(close_button)

        popup = Popup(
            title=self.ui_help_button,
            content=content, size_hint=(0.9, 0.9))
        close_button.bind(on_release=popup.dismiss)
        popup.open()

    def show_about_popup(self, *args):
        about_text = (
            f"[b]ShuffleTune - Renomeador de Arquivos[/b]\\n"
            f"Versão: 2.1\\n"
            f"Criado por: Inteligência Artificial\\n\\n"
            f"Um utilitário simples e poderoso para organizar suas coleções de arquivos."
        ) if self.language == 'pt' else (
            f"[b]ShuffleTune - File Renamer[/b]\\n"
            f"Version: 2.1\\n"
            f"Created by: Artificial Intelligence\\n\\n"
            f"A simple and powerful utility to organize your file collections."
        )

        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=about_text, markup=True, halign='center', valign='middle'))
        close_button = Button(text="OK", size_hint_y=None, height=dp(44))
        content.add_widget(close_button)
        
        popup = Popup(title=self.ui_about_button, content=content, size_hint=(0.8, 0.5))
        close_button.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == '__main__':
    ShuffleTuneApp().run()
