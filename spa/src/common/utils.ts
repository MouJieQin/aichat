// 格式化时间
export const formatTimeNow = () => {
    const time = new Date()
    return (
        time.getFullYear() + '-' +
        (time.getMonth() + 1).toString().padStart(2, '0') + '-' +
        time.getDate().toString().padStart(2, '0') + ' ' +
        time.getHours().toString().padStart(2, '0') + ':' +
        time.getMinutes().toString().padStart(2, '0') + ':' +
        time.getSeconds().toString().padStart(2, '0')
    )
}

// 添加样式类来高亮显示正在播放的句子
export const highlightPlayingSentence = (messageId: number, sentenceId: number) => {
    // 移除之前高亮的句子
    const previousHighlighted = document.querySelector('.sentence-playing')
    if (previousHighlighted) {
        previousHighlighted.classList.remove('sentence-playing')
    }

    // 如果sentence_id为-1，表示播放完毕，不需要高亮任何句子
    if (sentenceId === -1) {
        return
    }

    // 高亮当前播放的句子
    const selector = `.content[data-param1="${messageId}"][data-param2="${sentenceId}"]`
    const element = document.querySelector(selector)
    if (element) {
        element.classList.add('sentence-playing')
        // 滚动到高亮的句子
        // element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
}

export const scrollToBottom = () => {
    const scrollContainer =
        document.documentElement.scrollTop > 0
            ? document.documentElement
            : document.body;
    scrollContainer.scrollTop = scrollContainer.scrollHeight
}

export const mapLanguageCode = (lang?: string): string => {
    switch (lang) {
        case '日本語': return 'ja-JP'
        case '中文': return 'zh-CN'
        case 'English': return 'en-US'
        default: return 'zh-CN'
    }
}
