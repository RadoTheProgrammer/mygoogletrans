from google.cloud import translate_v2 as translat
def trans(text, target_language, source_language="fr"):
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language=target_language, source_language=source_language)
    return result
print(trans("Bonjour","Hello"))
