// markdown-processor
// 句子信息接口 
export interface SentenceInfo {
    text: string;
    messageId: number;
    sentenceId: number;
    isHeading?: boolean;
}

// 处理结果接口
export interface ProcessResult {
    html: string;
    sentences: SentenceInfo[];
}



export interface Message {
    message_id: number;
    raw_text: string;
    processed_html: string;
    sentences: Array<SentenceInfo>;
    time: string;
    role: 'user' | 'assistant' | 'system';
    is_playing: boolean;
}

export interface AIConfig {
    ai_avatar_url: string;
    base_url: string;
    api_key: string;
    model: string;
    temperature: number;
    max_tokens: number;
    context_max_tokens: number;
    max_messages: number;
    language: string;
    tts_voice: string;
    auto_play: boolean;
    auto_gen_title: boolean;
    speech_rate: number;
    suggestions?: string[];
}

// system config

export interface AppearanceConfig {
    theme: string;
    user_avatar_url: string;
}

export interface SpeakerConfig {
    audio_dir: string;
}

export interface AzureConfig {
    key: string;
    region: string;
}

export interface AiAssistantDefaultConfig {
    chat_title: string;
    system_prompt: string;
    ai_config_name: string;
}

export interface SystemAiConfig {
    ai_config_name: string;
}

export interface AiApiConfig {
    id: string;
    name: string;
    base_url: string;
    api_key: string;
    model: string;
    temperature: number;
    max_tokens: number;
    context_max_tokens: number;
    max_messages: number;
    language: string;
    tts_voice: string;
    auto_play: boolean;
    auto_gen_title: boolean;
    speech_rate: number;
    modelsOptional: string[];
}

export interface SystemConfig {
    appearance: AppearanceConfig;
    speaker: SpeakerConfig;
    azure: AzureConfig;
    ai_assistant: {
        default: AiAssistantDefaultConfig;
        system_ai_config: SystemAiConfig;
        apis: AiApiConfig[];
    };
}
