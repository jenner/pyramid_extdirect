import os
import glob
import mimetypes

class ImageHandler(object):
    """ a primitive image manager that store user picture on the disk """

    def __init__(self, base_path):
        self.base_path = base_path
        if not os.path.isdir(self.base_path):
            os.mkdir(self.base_path)

    def put(self, user, image):
        (mtype, encoding) = mimetypes.guess_type(image.filename)
        extension = mimetypes.guess_extension(mtype)
        user_dir = self.get_user_dir(user)
        if not os.path.isdir(user_dir):
            os.mkdir(user_dir)
        fname = 'picture{}'.format(extension)
        path = os.path.join(user_dir, fname)
        with open(path, 'w') as fp:
            input_file = image.file
            input_file.seek(0)
            while True:
                data = input_file.read(2<<16)
                if not data:
                    break
                fp.write(data)
        return fname

    def get_picture_path(self, user):
        if not user.picture:
            return None
        path = os.path.join(self.get_user_dir(user), user.picture)
        if not os.path.isfile(path):
            return None
        return path

    def get_user_dir(self, user):
        return os.path.join(self.base_path, str(user.id))

    def get_picture_type(self, user):
        pic_path = self.get_picture_path(user)
        if not pic_path:
            return None
        (mtype, encoding) = mimetypes.guess_type(pic_path)
        return mtype

