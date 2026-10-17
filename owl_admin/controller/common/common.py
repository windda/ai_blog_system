# -*- coding: utf-8 -*-
# @Author  : shaw-lee

"""
通用控制器：文件上传/下载/静态资源。

上传文件统一保存到配置项 profile 指定的目录；
提供 /uploads/article/<filename> 静态路由供前端访问图片。
"""

import os
import sys
import time
from flask import request, send_from_directory
from pydantic import Field
from typing_extensions import Annotated
from werkzeug.exceptions import NotFound
from werkzeug.utils import secure_filename

from owl_common.config import OWLConfig
from owl_common.constant import Constants
from owl_common.descriptor.serializer import JsonSerializer
from owl_common.descriptor.validator import FileValidator, QueryValidator
from owl_common.base.model import AjaxResponse, MultiFile
from owl_common.utils import FileUploadUtil, FileUtil, StringUtil
from owl_common.exception import FileUploadException, NotFoundException
from ... import reg

# 允许的图片后缀
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'}

# 单文件大小限制：5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@reg.api.route('/common/download')
@QueryValidator()
@JsonSerializer()
def common_download(
    file_name: Annotated[str, Field(min_length=1, max_length=100)],
    delete: Annotated[bool, Field(annotations=bool, default=False)],
):
    """文件下载"""
    try:
        response = send_from_directory(
            directory=OWLConfig.download_path,
            path=file_name,
            as_attachment=True,
        )
        if delete:
            FileUtil.delete_file(OWLConfig.download_path + file_name)
        return response
    except NotFound:
        raise NotFoundException("文件不存在")


@reg.api.route('/common/upload', methods=["POST"])
@JsonSerializer()
def common_upload():
    """
    图片上传接口
    接收 form-data 中 file 字段，保存到配置的 profile 路径下的 upload/article/
    返回：url（完整可访问URL）、fileName（相对路径）
    """
    if 'file' not in request.files:
        return AjaxResponse.from_error(msg="请求中没有 file 字段")

    file = request.files['file']
    if not file or file.filename == '':
        return AjaxResponse.from_error(msg="文件为空")

    # 校验后缀
    if not allowed_file(file.filename):
        msg = f"不支持的文件格式，支持: {', '.join(ALLOWED_EXTENSIONS)}"
        return AjaxResponse.from_error(msg=msg)

    # 校验文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_FILE_SIZE:
        return AjaxResponse.from_error(msg=f"文件大小不能超过 5MB")

    # 上传目录：使用配置的 profile 路径 + upload/article
    # 配置 profile = /home/wind/miniconda3/envs/ruoyi-vue-flask/uploads
    upload_base = OWLConfig.profile  # 来自配置 app.yml -> owl.profile
    upload_dir = os.path.join(upload_base, 'upload', 'article')

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = str(int(time.time() * 1000))
    safe_name = secure_filename(file.filename)
    new_filename = f"{timestamp}_{safe_name}"

    save_path = os.path.join(upload_dir, new_filename)
    file.save(save_path)

    # 返回可访问URL - 通过 Flask 路由 /uploads/article/<filename> 访问
    # 前端通过代理 /dev-api/uploads/article/xxx -> Flask /uploads/article/xxx
    file_relative_path = f"/uploads/article/{new_filename}"
    file_url = request.host_url.rstrip('/') + file_relative_path

    ajax_response = AjaxResponse.from_success()
    setattr(ajax_response, "url", file_url)
    setattr(ajax_response, "fileName", file_relative_path)
    setattr(ajax_response, "new_file_name", new_filename)
    setattr(ajax_response, "original_filename", file.filename)
    return ajax_response


def _upload_dir(*sub):
    """上传文件目录：打包环境用 exe 同目录（可写），开发环境用 profile 相对路径"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'uploads', *sub)
    base = os.path.join(OWLConfig.profile, *sub)
    # send_from_directory 对相对路径会基于 app.root_path 解析，导致与保存路径不一致，
    # 这里统一转成绝对路径（基于 cwd，与 file.save 保存时一致）
    if not os.path.isabs(base):
        base = os.path.abspath(base)
    return base


@reg.api.route('/uploads/article/<path:filename>')
def serve_upload(filename):
    """提供上传文件的静态访问（新目录：./uploads/upload/article/）"""
    return send_from_directory(_upload_dir('upload', 'article'), filename)


@reg.api.route('/uploads/avatar/<path:filename>')
def serve_avatar(filename):
    """提供头像文件的静态访问（目录：./uploads/avatar/）"""
    return send_from_directory(_upload_dir('avatar'), filename)


@reg.api.route('/static/upload/article/<path:filename>')
def serve_legacy_upload(filename):
    """兼容旧上传目录：owl_admin/static/upload/article/"""
    legacy_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'upload', 'article')
    return send_from_directory(legacy_dir, filename)


@reg.api.route('/common/uploads')
@FileValidator()
@JsonSerializer()
def common_uploads(files: MultiFile):
    """多文件上传"""
    file_names = []
    urls = []
    new_file_names = []
    original_filenames = []
    for _, file in files.items():
        file_name = FileUploadUtil.upload(file, OWLConfig.upload_path)
        file_names.append(file_name)
        url = request.host_url[:-1] + file_name
        urls.append(url)
        new_file_name = FileUploadUtil.get_filename(file_name)
        new_file_names.append(new_file_name)
        original_filenames.append(file.filename)

    ajax_response = AjaxResponse.from_success()
    setattr(ajax_response, "urls", ",".join(urls))
    setattr(ajax_response, "file_names", ",".join(file_names))
    setattr(ajax_response, "new_file_names", ",".join(new_file_names))
    setattr(ajax_response, "original_filenames", ",".join(original_filenames))
    return ajax_response


@reg.api.route('/common/download/resource')
@QueryValidator()
@JsonSerializer()
def common_download_resource(
    resource: Annotated[str, Field(annotation=str, min_length=1, max_length=100)]
):
    """资源下载"""
    download_path = OWLConfig.download_path + StringUtil.substring_after(resource, Constants.RESOURCE_PREFIX)
    try:
        response = send_from_directory(
            directory=OWLConfig.download_path,
            path=download_path,
            as_attachment=True,
        )
        return response
    except NotFound:
        raise NotFoundException("文件不存在")