# + Федорцова П.С.
# import config as config
import modules.config as config
# - Федорцова П.С.
def Toksik(data):
    text="У вас в тексте присутствует:\n"
    text_old=text[:]
    for key in data:
        # + Федорцова П.С.
        if key == "type_cyberbyllying":
            continue
        # - Федорцова П.С.
        if data[key] == 1:
            # + Федорцова П.С.
            # text+=config.TOXIC_NAMES[key]
            text+=f"- {config.TOXIC_NAMES[key]}\n"
            # - Федорцова П.С.
    if text==text_old:
        text+="ничего по токсичности\n"
    return text

def cyber(data,text=""):
    if text=="":
        text+="У вас в тексте присутствует:\n"
    # + Федорцова П.С.
    # text+=config.CYBERBULL_NAMES[data["type_cyberbullying"]]+"\n"
    cyberbullying_type = data.get("type_cyberbyllying", data.get("come_type"))
    text+=config.CYBERBULL_NAMES[cyberbullying_type]+"\n"
    # - Федорцова П.С.
    return text