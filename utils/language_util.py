import json
from os.path import join

from django.conf import settings


class LanguageUtil:
    language_codes = []


    def init_languages():
        languages = []

        file = open(join(settings.STATIC_ROOT, 'languages.json'))
        content = json.load(file)
        file.close()

        for language in content:
            languages.append(language)

        LanguageUtil.language_codes = languages