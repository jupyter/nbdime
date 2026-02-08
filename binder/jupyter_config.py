# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import logging

c.ServerApp.log_level = logging.DEBUG

c.ContentsManager.allow_hidden = True
# Use advance file ID service for out of band rename support
c.FileIdExtension.file_id_manager_class = "jupyter_server_fileid.manager.LocalFileIdManager"
