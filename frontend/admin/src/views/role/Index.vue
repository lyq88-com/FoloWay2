<template>
  <div class="role-page">
    <el-card shadow="never" class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <h3>AI角色管理</h3>
          <span class="toolbar-desc">管理AI虚拟角色的配置和表情素材</span>
        </div>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon> 新增角色
        </el-button>
      </div>
    </el-card>

    <!-- 角色卡片列表 -->
    <el-row :gutter="20" v-loading="loading">
      <el-col :xs="24" :sm="12" :lg="6" v-for="role in roleList" :key="role.id">
        <el-card shadow="hover" class="role-card">
          <div class="role-header">
            <div class="role-avatar" :style="{ background: getRoleColor(role.roleType) }">
              {{ getRoleEmoji(role.roleType) }}
            </div>
            <div class="role-title">
              <div class="role-name">{{ role.name }}</div>
              <el-tag size="small" :color="getRoleColor(role.roleType)" effect="dark">
                {{ getRoleTypeName(role.roleType) }}
              </el-tag>
            </div>
          </div>
          <div class="role-body">
            <div class="role-field">
              <span class="field-label">人格:</span>
              <span class="field-value">{{ role.personality }}</span>
            </div>
            <div class="role-field">
              <span class="field-label">描述:</span>
              <span class="field-value">{{ role.description }}</span>
            </div>
          </div>
          <div class="role-assets-preview">
            <div class="asset-item" v-for="emotion in getEmotionList()" :key="emotion.key">
              <span class="asset-emoji">{{ emotion.emoji }}</span>
              <span class="asset-label">{{ emotion.label }}</span>
            </div>
          </div>
          <div class="role-actions">
            <el-button size="small" @click="handleEditAssets(role)">素材管理</el-button>
            <el-button size="small" type="primary" @click="handleEdit(role)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(role)">删除</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 角色编辑弹窗 -->
    <el-dialog v-model="formVisible" :title="editingRole.id ? '编辑角色' : '新增角色'" width="600px">
      <el-form ref="formRef" :model="editingRole" :rules="formRules" label-width="100px">
        <el-form-item label="角色类型" prop="roleType">
          <el-select v-model="editingRole.roleType" placeholder="选择类型" style="width: 100%">
            <el-option label="可爱型 (cute)" value="cute" />
            <el-option label="温柔型 (gentle)" value="gentle" />
            <el-option label="严肃型 (serious)" value="serious" />
            <el-option label="活力型 (energetic)" value="energetic" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="editingRole.name" placeholder="如：小萌" />
        </el-form-item>
        <el-form-item label="人格描述" prop="personality">
          <el-input v-model="editingRole.personality" placeholder="如：可爱活泼，喜欢用emoji" />
        </el-form-item>
        <el-form-item label="选择页描述" prop="description">
          <el-input v-model="editingRole.description" type="textarea" :rows="2" placeholder="用户选择角色时看到的描述" />
        </el-form-item>
        <el-form-item label="系统提示词" prop="systemPrompt">
          <el-input v-model="editingRole.systemPrompt" type="textarea" :rows="4" placeholder="AI角色的系统提示词模板" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 素材管理弹窗 -->
    <el-dialog v-model="assetVisible" :title="`${currentRole?.name || ''} - 素材管理`" width="800px" top="5vh">
      <el-table :data="assetList" v-loading="assetLoading" border size="default">
        <el-table-column label="情绪状态" width="120">
          <template #default="{ row }">
            <div class="emotion-cell">
              <span class="emotion-emoji">{{ getEmotionEmoji(row.emotionStatus) }}</span>
              <span>{{ row.emotionText }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="bubbleText" label="气泡文字" min-width="200">
          <template #default="{ row }">
            <el-input v-model="row.bubbleText" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="动画类型" width="140">
          <template #default="{ row }">
            <el-select v-model="row.animationType" size="small" style="width: 100%">
              <el-option label="浮动 (float)" value="float" />
              <el-option label="弹跳 (bounce)" value="bounce" />
              <el-option label="摇晃 (shake)" value="shake" />
              <el-option label="脉冲 (pulse)" value="pulse" />
              <el-option label="无 (none)" value="none" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="素材URL" min-width="200">
          <template #default="{ row }">
            <el-input v-model="row.assetUrl" size="small" placeholder="图片/动画URL" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleSaveAsset(row)">保存</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import roleApi from '@/api/role'

const loading = ref(false)
const submitting = ref(false)
const assetLoading = ref(false)
const roleList = ref([])
const formVisible = ref(false)
const formRef = ref(null)
const assetVisible = ref(false)
const currentRole = ref(null)
const assetList = ref([])

const editingRole = reactive({
  id: null,
  roleType: '',
  name: '',
  personality: '',
  description: '',
  systemPrompt: ''
})

const formRules = {
  roleType: [{ required: true, message: '请选择角色类型', trigger: 'change' }],
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  personality: [{ required: true, message: '请输入人格描述', trigger: 'blur' }]
}

const roleConfig = {
  cute: { name: '可爱型', color: '#FF9800', emoji: '🐱' },
  gentle: { name: '温柔型', color: '#FFC107', emoji: '🌞' },
  serious: { name: '严肃型', color: '#607D8B', emoji: '🎯' },
  energetic: { name: '活力型', color: '#E91E63', emoji: '⚡' }
}

const emotionConfig = [
  { key: 'normal', label: '平静', emoji: '😊' },
  { key: 'happy', label: '开心', emoji: '😄' },
  { key: 'sad', label: '难过', emoji: '😢' },
  { key: 'gentle', label: '温柔', emoji: '🥰' },
  { key: 'encourage', label: '鼓励', emoji: '💪' },
  { key: 'chat', label: '聊天', emoji: '💬' }
]

const getRoleColor = (type) => roleConfig[type]?.color || '#909399'
const getRoleEmoji = (type) => roleConfig[type]?.emoji || '🤖'
const getRoleTypeName = (type) => roleConfig[type]?.name || type
const getEmotionList = () => emotionConfig
const getEmotionEmoji = (status) => emotionConfig.find(e => e.key === status)?.emoji || '❓'

const fetchList = async () => {
  loading.value = true
  try {
    const res = await roleApi.getRoleList()
    roleList.value = res.data.list
  } catch (e) {
    console.error('获取角色列表失败:', e)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  Object.assign(editingRole, {
    id: null, roleType: '', name: '', personality: '', description: '', systemPrompt: ''
  })
  formVisible.value = true
}

const handleEdit = (role) => {
  Object.assign(editingRole, {
    id: role.id, roleType: role.roleType, name: role.name,
    personality: role.personality, description: role.description,
    systemPrompt: role.systemPrompt || ''
  })
  formVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (editingRole.id) {
        await roleApi.updateRole(editingRole.id, { ...editingRole })
        ElMessage.success('更新成功')
      } else {
        await roleApi.createRole({ ...editingRole })
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

const handleDelete = async (role) => {
  try {
    await ElMessageBox.confirm(`确定要删除角色 "${role.name}" 吗？相关素材也将被删除。`, '警告', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await roleApi.deleteRole(role.id)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    // 用户取消
  }
}

const handleEditAssets = async (role) => {
  currentRole.value = role
  assetVisible.value = true
  assetLoading.value = true
  try {
    const res = await roleApi.getRoleAssets(role.id)
    assetList.value = res.data.list
  } catch (e) {
    console.error('获取素材失败:', e)
  } finally {
    assetLoading.value = false
  }
}

const handleSaveAsset = async (row) => {
  try {
    await roleApi.updateRoleAsset(currentRole.value.id, row.id, {
      bubbleText: row.bubbleText,
      animationType: row.animationType,
      assetUrl: row.assetUrl
    })
    ElMessage.success('素材已保存')
  } catch (e) {
    console.error('保存素材失败:', e)
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

.role-card {
  margin-bottom: 20px;

  :deep(.el-card__body) {
    padding: 20px;
  }
}

.role-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.role-avatar {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.role-title {
  .role-name {
    font-size: 18px;
    font-weight: 700;
    color: #303133;
    margin-bottom: 4px;
  }
}

.role-body {
  margin-bottom: 16px;
}

.role-field {
  margin-bottom: 8px;
  font-size: 13px;

  .field-label {
    color: #909399;
    margin-right: 6px;
  }
  .field-value {
    color: #303133;
  }
}

.role-assets-preview {
  display: flex;
  justify-content: space-around;
  padding: 12px 0;
  border-top: 1px dashed #e6e6e6;
  border-bottom: 1px dashed #e6e6e6;
  margin-bottom: 12px;
}

.asset-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  .asset-emoji {
    font-size: 22px;
  }
  .asset-label {
    font-size: 11px;
    color: #909399;
  }
}

.role-actions {
  display: flex;
  gap: 8px;

  .el-button {
    flex: 1;
  }
}

.emotion-cell {
  display: flex;
  align-items: center;
  gap: 6px;

  .emotion-emoji {
    font-size: 20px;
  }
}
</style>
