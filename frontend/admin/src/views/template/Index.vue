<template>
  <div class="template-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <h3>任务模板管理</h3>
          <span class="toolbar-desc">管理用户可选的习惯模板，包括图标、目标、难度等</span>
        </div>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon> 新增模板
        </el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table :data="templateList" v-loading="loading" stripe border style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column label="图标" width="60" align="center">
          <template #default="{ row }">
            <span style="font-size: 24px">{{ row.icon }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="140" />
        <el-table-column prop="type" label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :color="row.color" effect="dark">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="defaultTarget" label="默认目标" width="140" />
        <el-table-column label="难度" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.difficulty === 'easy' ? 'success' : row.difficulty === 'medium' ? 'warning' : 'danger'">
              {{ row.difficulty === 'easy' ? '简单' : row.difficulty === 'medium' ? '中等' : '困难' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="multiplier" label="倍率" width="80" align="center">
          <template #default="{ row }">{{ row.multiplier }}x</template>
        </el-table-column>
        <el-table-column prop="sortOrder" label="排序" width="80" align="center" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 模板编辑弹窗 -->
    <el-dialog v-model="formVisible" :title="editingTemplate.id ? '编辑模板' : '新增模板'" width="600px">
      <el-form ref="formRef" :model="editingTemplate" :rules="formRules" label-width="100px">
        <el-form-item label="图标" prop="icon">
          <el-input v-model="editingTemplate.icon" placeholder="emoji图标，如 💧" style="width: 100px" />
          <span class="icon-preview">{{ editingTemplate.icon }}</span>
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-input v-model="editingTemplate.type" placeholder="英文标识，如 morning/sport/read" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="editingTemplate.name" placeholder="如：早起一杯水" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editingTemplate.description" type="textarea" :rows="2" placeholder="习惯描述" />
        </el-form-item>
        <el-form-item label="默认目标" prop="defaultTarget">
          <el-input v-model="editingTemplate.defaultTarget" placeholder="如：喝200ml温水" />
        </el-form-item>
        <el-form-item label="颜色" prop="color">
          <el-color-picker v-model="editingTemplate.color" />
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-radio-group v-model="editingTemplate.difficulty">
            <el-radio value="easy">简单 (1.0x)</el-radio>
            <el-radio value="medium">中等 (1.5x)</el-radio>
            <el-radio value="hard">困难 (2.0x)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序" prop="sortOrder">
          <el-input-number v-model="editingTemplate.sortOrder" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch v-model="editingTemplate.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import templateApi from '@/api/template'

const loading = ref(false)
const submitting = ref(false)
const templateList = ref([])
const formVisible = ref(false)
const formRef = ref(null)

const editingTemplate = reactive({
  id: null,
  type: '',
  name: '',
  icon: '',
  description: '',
  defaultTarget: '',
  color: '#409EFF',
  difficulty: 'easy',
  multiplier: 1.0,
  sortOrder: 1,
  status: 1
})

const formRules = {
  icon: [{ required: true, message: '请输入图标', trigger: 'blur' }],
  type: [{ required: true, message: '请输入类型', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }],
  defaultTarget: [{ required: true, message: '请输入默认目标', trigger: 'blur' }]
}

const difficultyMultiplier = { easy: 1.0, medium: 1.5, hard: 2.0 }

const fetchList = async () => {
  loading.value = true
  try {
    const res = await templateApi.getTemplateList()
    templateList.value = res.data.list
  } catch (e) {
    console.error('获取模板列表失败:', e)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  Object.assign(editingTemplate, {
    id: null, type: '', name: '', icon: '', description: '',
    defaultTarget: '', color: '#409EFF', difficulty: 'easy',
    multiplier: 1.0, sortOrder: templateList.value.length + 1, status: 1
  })
  formVisible.value = true
}

const handleEdit = (row) => {
  Object.assign(editingTemplate, { ...row })
  formVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      editingTemplate.multiplier = difficultyMultiplier[editingTemplate.difficulty] || 1.0
      if (editingTemplate.id) {
        await templateApi.updateTemplate(editingTemplate.id, { ...editingTemplate })
        ElMessage.success('更新成功')
      } else {
        await templateApi.createTemplate({ ...editingTemplate })
        ElMessage.success('创建成功')
      }
      formVisible.value = false
      fetchList()
    } catch (e) {
      console.error('保存失败:', e)
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除模板 "${row.name}" 吗？`, '警告', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await templateApi.deleteTemplate(row.id)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    // 用户取消
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.toolbar-card {
  margin-bottom: 20px;

  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left {
  h3 {
    margin: 0;
    font-size: 18px;
    color: #303133;
  }
  .toolbar-desc {
    font-size: 13px;
    color: #909399;
    margin-top: 2px;
    display: block;
  }
}

.table-card {
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.icon-preview {
  font-size: 24px;
  margin-left: 12px;
  vertical-align: middle;
}
</style>
