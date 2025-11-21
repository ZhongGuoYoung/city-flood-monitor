<template>
  <div class="source-list">
    <!-- 添加视频源 -->
    <div class="add-source-btn" @click="openAddDialog">
      <i class="fas fa-plus"></i>
      <span>添加视频源</span>
    </div>

    <!-- 视频源列表 -->
    <div
      v-for="video in localVideos"
      :key="video.id"
      class="source-item"
      :class="{ active: selected && selected.id === video.id }"
      @click="select(video)"
    >
      <i class="fas fa-video"></i>
      <div class="source-info">
        <div class="source-name">{{ video.name }}</div>
        <div class="source-desc">{{ video.description }}</div>
      </div>
    </div>

    <!-- 添加对话框 -->
    <div class="modal-overlay" v-if="showDialog">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>添加视频源</h3>
          <button class="close-btn" @click="closeDialog">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <form @submit.prevent="confirmAdd">
            <div class="form-group">
              <label>来源类型</label>
              <div>
                <label style="margin-right:12px;">
                  <input type="radio" value="url" v-model="form.type"> 网络 URL
                </label>
                <label>
                  <input type="radio" value="file" v-model="form.type"> 本地文件
                </label>
                <label>
                  <input type="radio" value="image" v-model="form.type"> 本地图片
                </label>
              </div>
            </div>

            <div class="form-group">
              <label for="name">名称</label>
              <input id="name" v-model="form.name" required placeholder="请输入名称"/>
            </div>

            <div class="form-group" v-if="form.type === 'url'">
               <label for="url">视频URL</label>
               <input id="url" v-model="form.url" type="url" required placeholder="https://... 或 http://..."/>
             </div>

            <div class="form-group" v-else-if="form.type === 'file'">
               <label for="file">选择本地视频文件</label>
               <input id="file" type="file" accept="video/*" @change="onFileChange" required />
               <small v-if="form.file" style="color:#777;">
                 已选择：{{ form.file.name }}（{{ form.file.type || '未知类型' }}）
               </small>
             </div>

             <div class="form-group" v-else-if="form.type === 'image'">
                <label for="img">选择本地图片文件</label>
                <input id="img" type="file" accept="image/*" @change="onImgChange" required />
                <small v-if="form.imgFile" style="color:#777;">
                  已选择：{{ form.imgFile.name }}（{{ form.imgFile.type || '未知类型' }}）
                </small>
              </div>
            
            

            <div class="form-group">
              <label for="desc">描述</label>
              <textarea id="desc" v-model="form.description" rows="3" placeholder="可选"></textarea>
            </div>
          </form>
        </div>

        <div class="modal-footer">
          <button class="btn btn-cancel" @click="closeDialog">取消</button>
          <button class="btn btn-confirm" @click="confirmAdd">确认添加</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/* eslint-env vue/setup-compiler-macros */
import { reactive, ref, watch } from 'vue'

/**
 * Props：
 * - videos：父组件可传入列表。若传入，将与本地列表保持同步；
 * - selected：当前选中的视频源（可选，仅用于高亮）。
 */
const props = defineProps({
  videos: { type: Array, default: () => [] },
  selected: { type: Object, default: null }
})

/** Emits:
 * - update:videos  —— 当新增条目时把新数组回传父组件
 * - select-source —— 选中某个视频源时，向父抛出：{ type:'video', data }
 */
const emit = defineEmits(['update:videos', 'select-source'])

/** 内部状态（本地列表与对话框表单） */
const localVideos = ref([...props.videos])
watch(() => props.videos, v => { localVideos.value = [...v] }, { deep: true })

const showDialog = ref(false)
const form = reactive({ name: '', url: '', description: '', type: 'url', file: null, imgFile: null })

function openAddDialog(){
  form.name = ''
  form.url = ''
  form.description = ''
  form.type = 'url'
  form.file = null
  form.imgFile = null  
  showDialog.value = true
}
function closeDialog(){ showDialog.value = false }

function onImgChange(e){        
  const f = e.target?.files?.[0]
  form.imgFile = f || null
}
function confirmAdd(){
  //图片校验
   if (form.type === 'image'){
    if (!form.imgFile) return
    const url = URL.createObjectURL(form.imgFile)
    const item = {
      id: Date.now(),
      name: form.name?.trim() || form.imgFile.name,
      url,
      description: form.description || '',
      kind: 'image',               // 标记类型
      imgBlob: form.imgFile,       // 原始 File
      imgType: form.imgFile.type,  // MIME
      imgName: form.imgFile.name
    }
    const next = [...localVideos.value, item]
    localVideos.value = next
    emit('update:videos', next)
    // 告诉右侧：这是图片来源
    emit('select-source', { type: 'image', data: item })
    showDialog.value = false
    return
  }

  // 基础校验
  if (form.type === 'url'){
    if (!form.name || !form.url) return
  } else {
    if (!form.file) return
  }

  let url = form.url
  let name = form.name?.trim()
  let meta = {}

  if (form.type === 'file' && form.file){
    // 生成本地预览/播放的 blob URL
    url = URL.createObjectURL(form.file)
    if (!name) name = form.file.name

    // 关键：把 File 与 MIME 传出去，便于播放与上传后端
    meta = {
      local: true,
      fileName: form.file.name,
      fileType: form.file.type,   // e.g. 'video/mp4'
      fileBlob: form.file         // 原始 File
    }
  }

  const item = {
    id: Date.now(),
    name,
    url,
    description: form.description || '',
    ...meta
  }
  const next = [...localVideos.value, item]
  localVideos.value = next
  emit('update:videos', next)                     // 让父组件拿到新列表
  emit('select-source', { type: 'video', data: item })  // 直接选中新加的视频
  showDialog.value = false
}

function select(video){
  emit('select-source', { type: 'video', data: video })
}

function onFileChange(e){
  const files = e.target?.files
  form.file = files && files[0] ? files[0] : null
}
</script>

<style scoped>
/* 复用你原文件中的类名，确保样式风格一致 */
.source-list{ flex:1; padding:10px 0; overflow-y:auto; }
.add-source-btn{
  padding:15px 20px; cursor:pointer; transition:all .2s ease;
  display:flex; align-items:center; gap:12px; border:1px dashed rgba(255,255,255,.3);
  margin:10px; border-radius:4px; justify-content:center; color:#fff;
}
.add-source-btn:hover{ background-color:rgba(255,255,255,.1); border-color:#4fc3f7; }
.add-source-btn i{ font-size:1rem; color:#4fc3f7; }

.source-item{
  padding:15px 20px; cursor:pointer; transition:all .2s ease;
  border-left:4px solid transparent; display:flex; align-items:center; gap:12px; color:#fff;
}
.source-item:hover{ background-color:rgba(255,255,255,.1); }
.source-item.active{ background-color:rgba(79,195,247,.2); border-left-color:#4fc3f7; }
.source-item i{ font-size:1.2rem; color:#4fc3f7; }
.source-info{ flex:1; }
.source-name{ font-weight:500; margin-bottom:4px; }
.source-desc{ font-size:.8rem; opacity:.8; display:flex; align-items:center; gap:5px; }

/* 对话框 */
.modal-overlay{
  position:fixed; inset:0; background:rgba(0,0,0,.5);
  display:flex; align-items:center; justify-content:center; z-index:1000;
}
.modal-dialog{ background:#fff; border-radius:8px; width:90%; max-width:500px; max-height:90vh; overflow:auto; color:#333; }
.modal-header{
  padding:20px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center;
}
.modal-header h3{ margin:0; color:#1e3c72; }
.close-btn{ background:none; border:none; font-size:1.2rem; cursor:pointer; color:#666; }
.close-btn:hover{ color:#333; }
.modal-body{ padding:20px; }
.form-group{ margin-bottom:20px; }
.form-group label{ display:block; margin-bottom:8px; font-weight:500; color:#555; }
.form-group input,.form-group textarea{
  width:100%; padding:10px; border:1px solid #ddd; border-radius:4px; font-size:.9rem;
}
.form-group input:focus,.form-group textarea:focus{ outline:none; border-color:#4fc3f7; }
.modal-footer{ padding:20px; border-top:1px solid #eee; display:flex; justify-content:flex-end; gap:10px; }
.btn{ padding:8px 16px; border:none; border-radius:4px; cursor:pointer; font-size:.9rem; transition:background-color .3s; }
.btn-cancel{ background:#f5f5f5; color:#333; } .btn-cancel:hover{ background:#e0e0e0; }
.btn-confirm{ background:#1e3c72; color:#fff; } .btn-confirm:hover{ background:#2a5298; }
</style>
