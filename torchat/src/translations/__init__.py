import lang_en
import lang_de
import lang_hu
import lang_nl
import lang_fr
import lang_pl
import lang_pt
import lang_zh
import lang_bg
import lang_ru

# define all languages a user is allowed to choose from here:
SUPPORTED_LANGS = "en,de,hu,nl,fr,pl,pt,zh,bg,ru"

def getSupportedLanguages():
    return SUPPORTED_LANGS.split(",")