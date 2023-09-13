import telebot
from telebot import types
import requests 

TOKEN = '6420480020:AAE8qlvsf6ACVrvu33Y1Lk_rcl51LHgk95I'
bot = telebot.TeleBot(TOKEN)
administradores = [6400579411]
photo_no_enviar_fotos='prohibido.jpg'
temp_name = "temp.jpg"
database = "db.txt"

def getByFileId(file_id):
  return requests.get((bot.get_file_url(file_id)))

def saveMedia(response):
    with open(temp_name, 'wb') as photo_file:
        photo_file.write(response.content)

def getMedia():
    with open(temp_name, 'rb') as photo_file:
        return types.InputMediaPhoto(media=photo_file.read())

def getInfo(id):
  """Gets a dato by ID.

  Args:
    id: The ID of the dato to get.

  Returns:
    The dato with the specified ID.
  """

  with open(database, "r") as f:
    lines = f.readlines()

  for line in lines:
    data = line.split(":")
    if data[0] == id:
      return {
          "id": data[0],
          "chat_id": data[1],
          "file_id": data[2],
          "username": data[3],
          "comment": data[4].strip("\n")
      }

  return None

def addData(chat_id, file_id, username, comment):
  """Adds data to the file with autoincrementing ID.

  Args:
    chat_id: The chat ID of the dato.
    file_id: The file ID of the dato.
    username: The username of the dato.
    comment: comments
  Returns:
    The ID of the dato that was added.
  """

  with open(database, "r") as f:
    lines = f.readlines()

  if lines:
    last_id = int(lines[-1].split(":")[0])
  else:
    last_id = 0

  id = last_id + 1

  with open(database, "a") as f:
    f.write(f"{id}:{chat_id}:{file_id}:{username}:{comment}\n")

  return str(id)

def callMostrar(call, id, message_id):  
    isAdmin = call.from_user.id in administradores
    if (isAdmin):
        
        dato = getInfo(id)
        response = getByFileId(file_id=dato["file_id"])
        
        if dato["comment"]:
            caption = dato["comment"] + "\n" + "Foto enviada por: " + dato["username"]
        else:
            caption = "Foto enviada por: " + dato["username"]
        
        if response.status_code == 200:
            saveMedia(response=response)
            media=getMedia()
            
            bot.edit_message_media(chat_id=dato["chat_id"], message_id=message_id, media=media)
            bot.edit_message_caption(caption, dato["chat_id"], message_id)
    else:
        bot.answer_callback_query(call.id, "No eres Administrador, solo los administradores pueden usar estas funciones!", True)

def callPre(call, id):
  isAdmin = call.from_user.id in administradores

  if (isAdmin):
    dato = getInfo(id)
    
    bot.answer_callback_query(
      callback_query_id=call.id,
      text="Mira tu privado"
    )
    
    response = getByFileId(file_id=dato["file_id"])

    if response.status_code == 200:
        saveMedia(response=response)
        with open(temp_name, 'rb') as imagen_file:
            imagen_bytes = imagen_file.read()
        message_id=str(call.message.id)
        callMostrar = ":".join(["mostrar", id, message_id])
        buttonMostrar = types.InlineKeyboardButton('Mostrar foto', callback_data=callMostrar)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(buttonMostrar)
        if dato["comment"]:
            caption = dato["comment"] + "\n" + "Foto enviada por: " + dato["username"]
        else:
            caption = "Foto enviada por: " + dato["username"]
        bot.send_photo(
          chat_id=call.from_user.id, 
          photo=imagen_bytes, 
          caption=caption,  
          reply_markup=keyboard)
        
        
  else:
    bot.answer_callback_query(
      callback_query_id=call.id,
      text="Solo administradores pueden realizar esta accion.",
      show_alert=True
      )

# * Llamadas

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):  

        call_data_parts = call.data.split(":")
        callName, id, message_id = call_data_parts[0], call_data_parts[1], call_data_parts[2] if len(call_data_parts) > 2 else None
        
        if callName == "mostrar":
            callMostrar(call=call, id=id, message_id = message_id or call.message.id)
        elif callName == "previsualizar":
            callPre(call=call, id=id)
        
# * Recibir foto

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
  try:
      isAdmin = message.from_user.id in administradores
      if not isAdmin:  
          chat_id = str(message.chat.id)
          bot.delete_message(chat_id, message.message_id)
          
          # TODO: Validar si tiene username
          username = "@" + message.from_user.username if message.from_user.username != "None" else message.from_user.first_name
          
          
          id_db = addData(
            chat_id=chat_id,
            file_id=message.json['photo'][-1]['file_id'],
            username=username,
            comment= message.caption if message.caption is not None else ""
          )
          
          callMostrar = ":".join(["mostrar", id_db])
          callPre = ":".join(["previsualizar", id_db])
          
          buttonMostrar = types.InlineKeyboardButton('Mostrar foto', callback_data=callMostrar)
          buttonPre = types.InlineKeyboardButton('Previsualizar foto', callback_data=callPre)
          
          
          keyboard = types.InlineKeyboardMarkup()
          keyboard.add(buttonMostrar)
          keyboard.add(buttonPre)
          
          with open(photo_no_enviar_fotos, 'rb') as photo:
              bot.send_photo(chat_id, photo, caption="{} No se pueden enviar fotos!".format(username), reply_markup=keyboard)     
  except Exception as e:
      print(f"Se produjo una excepción en handle_photo:  {str(e)}")


if __name__ == "__main__":
    print("BOT LIVE!")
    bot.polling(none_stop=True)