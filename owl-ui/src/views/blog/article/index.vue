<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryForm" size="small" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="文章标题" prop="title">
        <el-input
          v-model="queryParams.title"
          placeholder="请输入文章标题"
          clearable
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item label="分类" prop="categoryId">
        <el-select v-model="queryParams.categoryId" placeholder="请选择" clearable>
          <el-option
            v-for="item in categoryOptions"
            :key="item.categoryId"
            :label="item.categoryName"
            :value="item.categoryId"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="文章状态" clearable>
          <el-option label="已发布" value="1" />
          <el-option label="草稿" value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="el-icon-plus"
          size="mini"
          @click="handleAdd"
          v-hasPermi="['blog:article:add']"
        >新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="el-icon-edit"
          size="mini"
          :disabled="single"
          @click="handleUpdate"
          v-hasPermi="['blog:article:edit']"
        >修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="el-icon-delete"
          size="mini"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['blog:article:remove']"
        >删除</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="articleList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="文章编号" align="center" prop="articleId" width="80" />
      <el-table-column label="封面" align="center" width="190">
        <template slot-scope="scope">
          <el-image
            v-if="scope.row.coverImage"
            :src="resolveImageUrl(scope.row.coverImage)"
            style="width: 170px; height: 96px; border-radius: 4px;"
            fit="cover"
          >
            <div slot="error" style="width:170px;height:96px;background:#f5f7fa;border-radius:4px;"></div>
          </el-image>
          <span v-else style="color:#c0c4cc;font-size:12px;">-</span>
        </template>
      </el-table-column>
      <el-table-column label="文章标题" align="center" prop="title" :show-overflow-tooltip="true" width="190" />
      <el-table-column label="分类" align="center" prop="categoryName" width="100" />
      <el-table-column label="作者" align="center" prop="authorName" width="100" />
      <el-table-column label="浏览量" align="center" prop="viewCount" width="70" />
      <el-table-column label="状态" align="center" prop="status" width="70">
        <template slot-scope="scope">
          <el-tag v-if="scope.row.status == '1'" type="success">已发布</el-tag>
          <el-tag v-else type="info">草稿</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="置顶" align="center" prop="isTop" width="60">
        <template slot-scope="scope">
          <el-tag v-if="scope.row.isTop == '1'" type="warning">置顶</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" align="center" prop="createTime" width="160">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button
            size="mini"
            type="text"
            icon="el-icon-edit"
            @click="handleUpdate(scope.row)"
            v-hasPermi="['blog:article:edit']"
          >修改</el-button>
          <el-button
            size="mini"
            type="text"
            icon="el-icon-delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['blog:article:remove']"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total>0"
      :total="total"
      :page.sync="queryParams.pageNum"
      :limit.sync="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加或修改文章对话框 -->
    <el-dialog :title="title" :visible.sync="open" width="800px" append-to-body>
      <el-form ref="form" :model="form" :rules="rules" label-width="80px">
        <el-row>
          <el-col :span="12">
            <el-form-item label="文章标题" prop="title">
              <el-input v-model="form.title" placeholder="请输入文章标题" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="categoryId">
              <el-select v-model="form.categoryId" placeholder="请选择分类" style="width: 100%">
                <el-option
                  v-for="item in categoryOptions"
                  :key="item.categoryId"
                  :label="item.categoryName"
                  :value="item.categoryId"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态">
              <el-radio-group v-model="form.status">
                <el-radio label="1">已发布</el-radio>
                <el-radio label="0">草稿</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="置顶">
              <el-radio-group v-model="form.isTop">
                <el-radio label="1">置顶</el-radio>
                <el-radio label="0">不置顶</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="标签">
              <el-select v-model="form.tagIds" multiple placeholder="请选择标签" style="width: 100%">
                <el-option
                  v-for="item in tagOptions"
                  :key="item.tagId"
                  :label="item.tagName"
                  :value="item.tagId"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="摘要" prop="summary">
              <el-input v-model="form.summary" type="textarea" :rows="2" placeholder="请输入摘要" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="封面图">
              <div>
                <el-upload
                  class="avatar-uploader"
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :show-file-list="false"
                  :on-success="handleCoverSuccess"
                  :before-upload="handleCoverBefore"
                >
                  <img v-if="form.coverImage" :src="resolveImageUrl(form.coverImage)" class="cover-preview" />
                  <i v-else class="el-icon-plus avatar-uploader-icon"></i>
                </el-upload>
                <el-button v-if="form.coverImage" type="danger" size="mini" icon="el-icon-delete" style="margin-left:8px;" @click="removeCover">删除封面</el-button>
              </div>
              <div class="el-upload__tip">建议尺寸 800x400，支持 jpg/png，不超过 5MB</div>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="内容" prop="content">
              <editor v-model="form.content" :min-height="300"/>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button type="primary" @click="submitForm">确 定</el-button>
        <el-button @click="cancel">取 消</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { listArticle, getArticle, delArticle, addArticle, updateArticle } from "@/api/blog/article";
import { listCategory } from "@/api/blog/category";
import { listTag } from "@/api/blog/tag";
import { getToken } from "@/utils/auth";

export default {
  name: "BlogArticle",
  data() {
    return {
      loading: true,
      ids: [],
      single: true,
      multiple: true,
      showSearch: true,
      total: 0,
      articleList: [],
      categoryOptions: [],
      tagOptions: [],
      title: "",
      open: false,
      uploadUrl: process.env.VUE_APP_BASE_API + "/common/upload",
      uploadHeaders: { Authorization: "Bearer " + getToken() },
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        title: undefined,
        categoryId: undefined,
        status: undefined
      },
      form: {},
      rules: {
        title: [
          { required: true, message: "文章标题不能为空", trigger: "blur" }
        ],
        categoryId: [
          { required: true, message: "请选择分类", trigger: "change" }
        ],
        content: [
          { required: true, message: "文章内容不能为空", trigger: "blur" }
        ]
      }
    };
  },
  created() {
    this.getList();
    this.getCategoryOptions();
    this.getTagOptions();
  },
  methods: {
    getList() {
      this.loading = true;
      listArticle(this.queryParams).then(response => {
        this.articleList = response.rows;
        this.total = response.total;
        this.loading = false;
      });
    },
    getCategoryOptions() {
      listCategory({ pageNum: 1, pageSize: 100 }).then(response => {
        this.categoryOptions = response.rows;
      });
    },
    getTagOptions() {
      listTag({ pageNum: 1, pageSize: 100 }).then(response => {
        this.tagOptions = response.rows;
      });
    },
    cancel() {
      this.open = false;
      this.reset();
    },
    reset() {
      this.form = {
        articleId: undefined,
        title: undefined,
        content: undefined,
        summary: undefined,
        categoryId: undefined,
        status: "0",
        isTop: "0",
        tagIds: []
      };
      this.resetForm("form");
    },
    handleQuery() {
      this.queryParams.pageNum = 1;
      this.getList();
    },
    resetQuery() {
      this.resetForm("queryForm");
      this.handleQuery();
    },
    handleSelectionChange(selection) {
      this.ids = selection.map(item => item.articleId);
      this.single = selection.length != 1;
      this.multiple = !selection.length;
    },
    handleAdd() {
      this.reset();
      this.open = true;
      this.title = "添加文章";
    },
    handleUpdate(row) {
      this.reset();
      const articleId = row.articleId || this.ids;
      getArticle(articleId).then(response => {
        this.form = response.data;
        this.form.tagIds = (response.data.tags || []).map(t => t.tagId);
        this.open = true;
        this.title = "修改文章";
      });
    },
    submitForm: function() {
      this.$refs["form"].validate(valid => {
        if (valid) {
          if (this.form.articleId != undefined) {
            updateArticle(this.form).then(response => {
              this.$modal.msgSuccess("修改成功");
              this.open = false;
              this.getList();
            });
          } else {
            addArticle(this.form).then(response => {
              this.$modal.msgSuccess("新增成功");
              this.open = false;
              this.getList();
            });
          }
        }
      });
    },
    handleDelete(row) {
      const articleIds = row.articleId || this.ids;
      this.$modal.confirm('是否确认删除文章编号为"' + articleIds + '"的数据项？').then(function() {
        return delArticle(articleIds);
      }).then(() => {
        this.getList();
        this.$modal.msgSuccess("删除成功");
      }).catch(() => {});
    },
    handleCoverSuccess(res, file) {
      console.log("[封面图上传返回]", res);
      if (res.code === 200) {
        // 只存相对路径（如 /uploads/article/xxx.png），前端展示时统一加前缀
        this.form.coverImage = res.fileName;
        console.log("[封面图赋值]", this.form.coverImage);
        this.$message.success("封面上传成功");
      } else {
        this.$message.error("封面上传失败: " + (res.msg || '未知错误'));
      }
    },
    removeCover() {
      this.form.coverImage = '';
      this.$message.success("封面已删除");
    },
    /**
     * 智能解析图片URL：兼容新旧存储格式
     * - 新格式（相对路径 /uploads/article/xxx.png）→ 拼接 BASE_API 通过代理访问
     * - 旧格式（已含 /dev-api 前缀）→ 直接使用
     * - 其他绝对路径 → 直接使用
     */
    resolveImageUrl(path) {
      if (!path) return '';
      // 已经是绝对 URL（http/https 开头）直接返回
      if (path.startsWith('http://') || path.startsWith('https://')) return path;
      // 旧格式：已经包含 /dev-api 前缀
      if (path.startsWith('/dev-api/')) return path;
      // 新格式：相对路径，拼接 BASE_API
      return process.env.VUE_APP_BASE_API + path;
    },
    handleCoverBefore(file) {
      const isImage = file.type === 'image/jpeg' || file.type === 'image/png';
      const isLt5M = file.size / 1024 / 1024 < 5;
      if (!isImage) {
        this.$message.error('只能上传 jpg/png 格式的图片');
        return false;
      }
      if (!isLt5M) {
        this.$message.error('图片大小不能超过 5MB');
        return false;
      }
      return true;
    }
  }
};
</script>

<style scoped>
  .avatar-uploader .el-upload {
    border: 1px dashed #d9d9d9;
    border-radius: 6px;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    width: 360px;
    height: 180px;
  }
  .avatar-uploader .el-upload:hover {
    border-color: #409eff;
  }
  .avatar-uploader-icon {
    font-size: 28px;
    color: #8c939d;
    width: 360px;
    height: 180px;
    line-height: 180px;
    text-align: center;
  }
  .cover-preview {
    width: 100%;
    max-width: 320px;
    height: 180px;
    display: block;
    object-fit: cover;
  }
</style>
