<template>
  <div class="ezviz-player">
    <div class="header">
      <i class="fas fa-video"></i>
      <span>{{ title }}</span>
    </div>

    <div ref="videoPlayer" class="video-container"></div>

    <div class="controls">
      <button @click="reloadPlayer">重新加载</button>
      <button @click="toggleLightweight">
        {{ localLightweight ? '切换至标准模式' : '切换至轻量模式' }}
      </button>
    </div>

    <div v-if="error" class="error-msg">
      {{ error }}
    </div>
  </div>
</template>

<script>
export default {
  name: "EzvizPlayer",

  props: {
    /** 萤石云 AccessToken */
    accessToken: {
      type: String,
      required: true,
    },
    /** 视频流地址：支持 EZOpen 或 RTSP */
    url: {
      type: String,
      required: true,
    },
    /** 显示标题 */
    title: {
      type: String,
      default: "实时监控",
    },
    /** 父组件可传入轻量模式标记 */
    lightweight: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      player: null,
      localLightweight: this.lightweight, // ✅ 用本地变量代替
      error: "",
    };
  },

  mounted() {
    this.initPlayer();
  },

  methods: {
    initPlayer() {
      // 检查 EZUIKit SDK 是否加载
      if (!window.EZUIKit || !window.EZUIKit.EZUIPlayer) {
        this.error = "EZUIKit SDK 未加载，请检查 public/index.html 是否正确引入。";
        console.error(this.error);
        return;
      }

      try {
        // ✅ 初始化播放器
        this.player = new window.EZUIKit.EZUIPlayer({
          id: this.$refs.videoPlayer,
          accessToken: this.accessToken,
          url: this.url,
          autoplay: true,
          width: this.localLightweight ? 320 : 600,
          height: this.localLightweight ? 180 : 400,
        });

        this.player.on("error", (e) => {
          console.error("播放错误:", e);
          this.error = "视频加载失败，请检查设备状态或网络连接。";
        });

        this.player.on("play", () => {
          console.log("视频播放中...");
        });
      } catch (e) {
        console.error(e);
        this.error = "初始化播放器时出错。";
      }
    },

    reloadPlayer() {
      if (this.player) {
        this.player.stop();
        this.player = null;
      }
      this.error = "";
      this.$nextTick(() => this.initPlayer());
    },

    toggleLightweight() {
      this.localLightweight = !this.localLightweight;
      this.reloadPlayer();
    },
  },
};
</script>

<style scoped>
.ezviz-player {
  background-color: #fff;
  border-radius: 10px;
  padding: 15px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
}

.header {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e3c72;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.video-container {
  width: 100%;
  height: auto;
  background-color: #000;
  border-radius: 6px;
  overflow: hidden;
}

.controls {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.controls button {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background-color: #1e3c72;
  color: white;
  cursor: pointer;
  transition: 0.2s;
}

.controls button:hover {
  background-color: #2a5298;
}

.error-msg {
  color: #f44336;
  font-size: 0.9rem;
  margin-top: 8px;
}
</style>
