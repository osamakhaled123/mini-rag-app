import os

class TemplateParser:
    def __init__(self, default_language: str = "en", language: str = None):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.language = language
        self.default_language = default_language
        self.language_path=None
        
        self.set_langauge(language)
        
    def set_langauge(self, language: str):
        target_lang = language or self.default_language
        self.language_path = os.path.join(self.current_path, "locales", target_lang)
        
        if os.path.exists(self.language_path):
            self.language = target_lang

        else:
            self.language = self.default_language
            self.language_path = os.path.join(
                self.current_path, "locales", self.language
            )

                    #rag        docorsystem     #variables
    def get(self, group: str, key: str, vars: dict={}):
        if not group or not key:
            return None
        
        group_path = os.path.join(self.language_path, f"{group}.py")
        if not os.path.exists(group_path):
            self.language = self.default_language
            self.language_path = os.path.join(self.current_path, "locales", self.language)
            group_path = os.path.join(self.language_path, f"{group}.py")
            
            if not os.path.exists(group_path):
                return None
            
        module_name = f"stores.llm.templates.locales.{self.language}.{group}"
        
        try:
            module = __import__(module_name, fromlist=[group])
        except ImportError:
            return None
        
        key_attribute = getattr(module, key, None)
        
        if not key_attribute:
            return None
        
        return key_attribute.substitute(vars)