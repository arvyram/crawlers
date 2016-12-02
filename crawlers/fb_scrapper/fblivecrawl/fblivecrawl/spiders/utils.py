
class Utils:
     @classmethod
     def str_to_dict( cls, html_text ):
         ret_dict = {}
         html_text = html_text.replace('"', '').replace('\\', '')
         html_text = html_text.replace('{', '').replace('}', '')
         for texts in html_text.split(','):
            if ':' in texts and len( texts.split(':') )== 2:
                param = texts.split(':')
                ret_dict[param[0]] = param[1]
         return ret_dict
         
