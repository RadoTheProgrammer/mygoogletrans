import googletrans,s
translator=googletrans.Translator(service_urls=[
       'translate.google.com',

     ])

txt=translator.translate("Bonjour","en")
