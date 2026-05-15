import vk_api
from vk_api import VkUpload
from config import TOKEN

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
upload = VkUpload(vk_session)

photos = {
    'welcome': 'welcome.jpg',
    'instruction': 'instruction.jpg',
    'rules': 'rules.jpg',
    'locations': 'locations.jpg',
    'thanks': 'thanks.jpg',
}

for name, filename in photos.items():
    photo = upload.photo_messages(photos=filename)[0]
    attachment = f"photo{photo['owner_id']}_{photo['id']}"
    print(f"{name}: {attachment}")