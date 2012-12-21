# -*- coding: UTF-8 -*-

##############################################################################
#                                                                            #
# Copyright (c) 2007-2010 Bernd Kreuss <prof7bit@gmail.com>                  #
#                                                                            #
# Translation file for TorChat                                               #
#                                                                            #
##############################################################################

LANGUAGE_CODE = u"ru"
LANGUAGE_NAME = u"Русский"
LANGUAGE_NAME_ENGLISH = u"Russian"
TRANSLATOR_NAMES = [u"SB14.org, RusInfo.cc"]

#buttons
BTN_CANCEL = u"Отмена"
BTN_OK = u"Да"
BTN_SAVE_AS = u"Сохранить как..."
BTN_CLOSE = u"Закрыть"

#status
ST_AVAILABLE = u"В сети"
ST_AWAY = u"Отсутствую"
ST_EXTENDED_AWAY = u"Недоступен"
ST_OFFLINE = u"Отключен"

#TaskbarMenu
MTB_SHOW_HIDE_TORCHAT = u"Показать/Скрыть TorChat"
MTB_QUIT = u"Выход"

#popup menu
MPOP_CHAT = u"Чат..."
MPOP_SEND_FILE = u"Послать файл..."
MPOP_EDIT_CONTACT = u"Редактировать контакт..."
MPOP_DELETE_CONTACT = u"Удалить контакт..."
MPOP_SHOW_OFFLINE_MESSAGES = u"Показать очередь оффлайн сообщений"
MPOP_CLEAR_OFFLINE_MESSAGES = u"Очистить очередь оффлайн сообщений"
MPOP_ACTIVATE_LOG = u"Задействовать ведение лога"
MPOP_STOP_LOG = u"Остановить ведение лога"
MPOP_DELETE_EXISTING_LOG = u"Удалить существующий лог-файл"
MPOP_DELETE_AND_STOP_LOG = u"Удалить лог и остановить логгирование"
MPOP_ADD_CONTACT = u"Добавить контакт"
MPOP_ABOUT = u"О программе TorChat"
MPOP_ASK_AUTHOR = u"Спросить %s..."
MPOP_SETTINGS = u"Установки..."
MPOP_EDIT_MY_PROFILE = u"Редактировать мой профиль..."
# MPOP_COPY_ID_TO_CLIPBOARD=u"Copy ID to clipboard"

#chat window popup menu
CPOP_COPY = u"Копировать"

#confirm delete message box
D_CONFIRM_DELETE_TITLE = u"Подтвердить удаление"
D_CONFIRM_DELETE_MESSAGE = u"Действительно удалить этот контакт?\n(%s %s)"

#warning about log
D_LOG_WARNING_TITLE = u"Ведение лога TorChat активно"
D_LOG_WARNING_MESSAGE = u"Запись лога в файл включена!\n\nLog File: %s\n\nПомните, что нужно удалить лог-файл, когда вы закончите отладку. Этот файл может содержать потенциально опасную важную информацию."

#warning about used port
D_WARN_USED_PORT_TITLE = u"TorChat: Порт занят"
D_WARN_USED_PORT_MESSAGE = u"Какое-то приложение, скорее всего другой экземпляр TorChat, уже использует %s:%s. Вы должны создать еще один профиль с использованием других портов, чтобы запускать несколько экземпляров TorChat одновременно."

#warnig about unread messages
D_WARN_UNREAD_TITLE = u"TorChat: Непрочитанные сообщения"
D_WARN_UNREAD_MESSAGE = u"У вас есть непрочитанные сообщения.\nОни будут утеряны навсегда!\n\nВы действительно хотите выйти из TorChat сейчас?"

#warning about offline buddy
D_WARN_BUDDY_OFFLINE_TITLE = u"TorChat: Контакт не в сети"
D_WARN_BUDDY_OFFLINE_MESSAGE = u"Это операция невозможна, если контакт не в сети"

#warning about multiple files
D_WARN_FILE_ONLY_ONE_TITLE = u"TorChat: Несколько файлов"
D_WARN_FILE_ONLY_ONE_MESSAGE = u"Вы не можете передавать несколько файлов одновременно. Посылайте файлы по одному или используйте архивы."

#warning about file save error
D_WARN_FILE_SAVE_ERROR_TITLE = u"TorChat: Невозможно сохранить файл"
D_WARN_FILE_SAVE_ERROR_MESSAGE = u"Файл '%s' не может быть создан.\n\n%s"

#warning about file already exists
D_WARN_FILE_ALREADY_EXISTS_TITLE = u"TorChat: Файл существует"
D_WARN_FILE_ALREADY_EXISTS_MESSAGE = u"Файл '%s' уже есть.\nПерезаписать?"

#dialog: add/edit contact
DEC_TITLE_ADD = u"Добавить контакт"
DEC_TITLE_EDIT = u"Редактировать контакт"
DEC_TORCHAT_ID = u"TorChat ID"
DEC_DISPLAY_NAME = u"Отображаемое имя"
DEC_INTRODUCTION = u"Текст приветствия"
DEC_MSG_16_CHARACTERS = u"Адрес должен быть длиной 16 символов, а не %i."
DEC_MSG_ONLY_ALPANUM = u"Адрес может содержать только цифры и буквы в нижнем регистре"
DEC_MSG_ALREADY_ON_LIST = u"%s уже в списке"

#dialog: edit my profile
DEP_TITLE = u"Редактировать профиль"
DEP_NAME = u"Имя"
DEP_TEXT = u"Текст"
DEP_SET_AVATAR = u"Установить аватар"
DEP_REMOVE_AVATAR = u"Убрать аватар"
DEP_AVATAR_SELECT_PNG = u"Выберите .PNG файл для аватара. Изображение будет отмасштабировано до 64*64, может содержать прозрачность"
DEP_PNG_FILES = u"PNG файлы"
DEP_ALL_FILES = u"Все файлы"
DEP_WARN_TITLE = u"Выбор аватара невозможен"
DEP_WARN_IS_ALREADY = u"Этот аватар уже используется"
DEP_WARN_MUST_BE_PNG = u"Аватар должен быть .png файлом"

#file transfer window
DFT_FILE_OPEN_TITLE = u"Послать файл %s"
DFT_FILE_SAVE_TITLE = u"Принять файл от %s"
DFT_SEND = u"Отправка %s\n %s\n%04.1f%% (%i из %i байт(-а))"
DFT_RECEIVE = u"Получение %s\n от %s\n%04.1f%% (%i из %i байт(-а))"
DFT_WAITING = u"ожидание подключения"
DFT_STARTING = u"запуск передачи"
DFT_ABORTED = u"передача прервана"
DFT_COMPLETE = u"передача завершена"
DFT_ERROR = u"ошибка"

#settings dialaog
DSET_TITLE = u"Конфигурация TorChat"
DSET_NET_TITLE = u"Сеть"
DSET_NET_ACTIVE = u"активно"
DSET_NET_INACTIVE = u"неактивно"
DSET_NET_TOR_ADDRESS = u"Tor прокси адрес"
DSET_NET_TOR_SOCKS = u"Socks порт"
DSET_NET_TOR_CONTROL = u"Порт контроллера"
DSET_NET_OWN_HOSTNAME = u"Собственный TorChat-ID"
DSET_NET_LISTEN_INTERFACE = u"Интерфейс"
DSET_NET_LISTEN_PORT = u"Порт"
DSET_GUI_TITLE = u"Внешний вид"
DSET_GUI_LANGUAGE = u"Язык"
DSET_GUI_OPEN_MAIN_HIDDEN = u"Запускать со свернутым главным окном"
DSET_GUI_OPEN_CHAT_HIDDEN = u"Не открывать автоматически новые окна"
DSET_GUI_NOTIFICATION_POPUP = u"Всплывающие подсказки"
DSET_GUI_NOTIFICATION_METHOD = u"Вид подсказок"
DSET_GUI_FLASH_WINDOW = u"Мигать заголовком окна при получении нового сообщения"
DSET_MISC_TITLE = u"Разное"
DSET_MISC_TEMP_IN_DATA = u"Хранить временные файлы внутри папки с программой"
DSET_MISC_TEMP_CUSTOM_DIR = u"Папка для временных файлов (оставьте пустой для папки по-умолчанию)"

#notices in the chat window (those in square brackets)
NOTICE_DELAYED_MSG_WAITING = u"отложенные сообщения ждут отправки"
NOTICE_DELAYED_MSG_SENT = u"отложенные сообщения отправлены"
NOTICE_DELAYED = u"отложено"

#messagebox for offline messages
MSG_OFFLINE_TITLE = u"TorChat: сообщения в очереди"
MSG_OFFLINE_EMPTY = u"(больше) нет сообщений в очереди для %s"
MSG_OFFLINE_QUEUED = u"сообщения в очереди для %s:\n\n%s"

#buddy list mouse hover popup
BPOP_BUDDY_IS_OFFLINE = u"Контакт не в сети"
BPOP_CONNECTED_AWAITING_RETURN_CONN = u"Соединено, ожидаем взаимного соединения..."
BPOP_CLIENT_SOFTWARE = u"Клиент: %s %s"

#logging of conversations to file
LOG_HEADER = u"Этот лог файл не подписан и не является неоспоримым доказательством"
LOG_STARTED = u"Запись начата"
LOG_STOPPED = u"Запись закончена"
LOG_DELETED = u"Лог-файлы удалены"
LOG_IS_ACTIVATED = u"Запись лог-файла включена:\n%s"
LOG_IS_STOPPED_OLD_LOG_FOUND = u"Логгирование выключено, но старый лог-файл все еще существует:\n%s"

#about box
ABOUT_TITLE = u"О программе TorChat"

# #new strings
# D_WARN_CLOSE_CHATWINDOW_TITLE = u"Torchat: Close chatwindow?"
# D_WARN_CLOSE_CHATWINDOW_MESSAGE = u"Are you sure you want to close this window?"
# D_WARN_CONTROL_CONNECTION_FAILED_TITLE = u"Connection failed"
# D_WARN_CONTROL_CONNECTION_FAILED_MESSAGE = u"The control connection has failed.\nWe could not change the TOR-identity."
# DSET_GUI_CONFIRM_CLOSE_CHATWINDOW = u"Confirm before closing a chatwindow"
# DSET_GUI_CHATLOG_PATH = u"Chatlog directory"
# DSET_GUI_GLOBAL_CHATLOGS = u"Save chatlogs for all contacts"
# DSET_GUI_CLEAR_CACHE_STARTUP = u"Clear TOR-cache on start-up (tor_data)"
# DSET_NET_TOR_PASS = u"Control password"
# DSET_FILES_TITLE = u"Files"
# DSET_FILES_SEP_AUTOSAVE_TITLE = u"Saving files"
# DSET_MISC_FILES_CUSTOM_DIR = u"Downloads folder"
# DSET_MISC_FILES_CUSTOM_DIR_INFO = u"If you want torchat to automatically save incoming files, select the folder here. If you want to manually save each file, leave it empty."
# DEC_NEW_IDENTITIY = u"Use a new identity"
# TOOL_SETTINGS_LABEL = u"Settings"
# TOOL_SETTINGS_HELP = u"Open the settings"
# TOOL_ADD_CONTACT_LABEL = u"Add contact"
# TOOL_ADD_CONTACT_HELP = u"Add a new contact"
# TOOL_EDIT_PROFILE_LABEL = u"Edit profile"
# TOOL_EDIT_PROFILE_HELP = u"Edit your profile"
# TOOL_NEW_IDENTITY_LABEL = u"New identity"
# TOOL_NEW_IDENTITY_HELP = u"Use a new identity"