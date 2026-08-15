<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryForm" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="评论内容" prop="content">
        <el-input
          v-model="queryParams.content"
          placeholder="请输入评论内容"
          clearable
          size="mini"
          @keyup.enter.native="handleQuery"
        />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="评论状态" clearable size="mini">
          <el-option label="待审核" value="0" />
          <el-option label="已通过" value="1" />
          <el-option label="已驳回" value="2" />
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
          type="danger"
          plain
          icon="el-icon-delete"
          size="mini"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['blog:comment:remove']"
        >删除</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="commentList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="评论编号" align="center" prop="commentId" width="80" />
      <el-table-column label="文章编号" align="center" prop="articleId" width="80" />
      <el-table-column label="文章标题" align="center" prop="articleTitle" width="180" :show-overflow-tooltip="true">
        <template slot-scope="scope">
          <span v-if="scope.row.articleTitle">{{ scope.row.articleTitle }}</span>
          <span v-else style="color:#c0c4cc;">（已删除）</span>
        </template>
      </el-table-column>
      <el-table-column label="评论者" align="center" prop="authorName" width="100" />
      <el-table-column label="评论内容" min-width="200">
        <template slot-scope="scope">
          <div class="content-cell" @click="showDetail(scope.row)">
            <span class="content-text">{{ scope.row.content }}</span>
            <el-link v-if="isLongContent(scope.row.content)" type="primary" :underline="false" style="margin-left: 4px;">详情</el-link>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" align="center" prop="status" width="80">
        <template slot-scope="scope">
          <el-tag v-if="scope.row.status == '0'" type="warning">待审核</el-tag>
          <el-tag v-else-if="scope.row.status == '1'" type="success">已通过</el-tag>
          <el-tag v-else type="danger">已驳回</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="评论时间" align="center" prop="createTime" width="160">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="180" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button
            size="mini"
            type="text"
            icon="el-icon-view"
            @click="showDetail(scope.row)"
          >详情</el-button>
          <el-button
            v-if="scope.row.status == '0'"
            size="mini"
            type="text"
            icon="el-icon-check"
            @click="handleApprove(scope.row)"
            v-hasPermi="['blog:comment:edit']"
          >通过</el-button>
          <el-button
            v-if="scope.row.status == '0'"
            size="mini"
            type="text"
            icon="el-icon-close"
            style="color: #f56c6c;"
            @click="handleReject(scope.row)"
            v-hasPermi="['blog:comment:edit']"
          >驳回</el-button>
          <el-button
            size="mini"
            type="text"
            icon="el-icon-delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['blog:comment:remove']"
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

    <!-- 评论详情弹窗 -->
    <el-dialog title="评论详情" :visible.sync="detailOpen" width="600px" append-to-body>
      <div v-if="detailRow" class="comment-detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="评论编号">{{ detailRow.commentId }}</el-descriptions-item>
          <el-descriptions-item label="文章编号">{{ detailRow.articleId }}</el-descriptions-item>
          <el-descriptions-item label="文章标题">{{ detailRow.articleTitle || '（已删除）' }}</el-descriptions-item>
          <el-descriptions-item label="评论者">{{ detailRow.authorName || '未知' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag v-if="detailRow.status == '0'" type="warning" size="small">待审核</el-tag>
            <el-tag v-else-if="detailRow.status == '1'" type="success" size="small">已通过</el-tag>
            <el-tag v-else type="danger" size="small">已驳回</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="评论时间">{{ parseTime(detailRow.createTime) }}</el-descriptions-item>
          <el-descriptions-item label="评论内容" :span="2">
            <div class="detail-content">{{ detailRow.content }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <div slot="footer" class="dialog-footer">
        <el-button @click="detailOpen = false">关 闭</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { listComment, delComment, updateCommentStatus } from "@/api/blog/comment";

export default {
  name: "BlogComment",
  data() {
    return {
      loading: true,
      ids: [],
      single: true,
      multiple: true,
      showSearch: true,
      total: 0,
      commentList: [],
      title: "",
      open: false,
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        content: undefined,
        status: undefined
      },
      form: {},
      detailOpen: false,
      detailRow: null
    };
  },
  created() {
    this.getList();
  },
  methods: {
    getList() {
      this.loading = true;
      listComment(this.queryParams).then(response => {
        this.commentList = response.rows;
        this.total = response.total;
        this.loading = false;
      });
    },
    cancel() {
      this.open = false;
      this.reset();
    },
    reset() {
      this.form = {};
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
      this.ids = selection.map(item => item.commentId);
      this.single = selection.length != 1;
      this.multiple = !selection.length;
    },
    handleDelete(row) {
      const commentIds = row.commentId || this.ids;
      this.$modal.confirm('是否确认删除评论编号为"' + commentIds + '"的数据项？').then(function() {
        return delComment(commentIds);
      }).then(() => {
        this.getList();
        this.$modal.msgSuccess("删除成功");
      }).catch(() => {});
    },
    handleApprove(row) {
      updateCommentStatus({ commentId: row.commentId, status: '1' }).then(() => {
        this.$modal.msgSuccess("审核通过");
        this.getList();
      }).catch(() => {
        this.$modal.msgError("审核失败");
      });
    },
    handleReject(row) {
      updateCommentStatus({ commentId: row.commentId, status: '2' }).then(() => {
        this.$modal.msgSuccess("已驳回");
        this.getList();
      }).catch(() => {
        this.$modal.msgError("驳回失败");
      });
    },
    isLongContent(content) {
      return content && content.length > 50;
    },
    showDetail(row) {
      this.detailRow = row;
      this.detailOpen = true;
    }
  }
};
</script>

<style scoped>
.content-cell {
  cursor: pointer;
  display: flex;
  align-items: flex-start;
}
.content-text {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-all;
  line-height: 1.5;
  flex: 1;
}
.content-cell:hover .content-text {
  color: #409eff;
}
.detail-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.8;
  max-height: 400px;
  overflow-y: auto;
}
</style>