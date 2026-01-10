// 冰川蓝与火烈鸟红色系主题配置（低饱和度）
export const glacierTheme = {
  // 主色调 - 冰川蓝与火烈鸟红（低饱和度）
  colors: {
    primary: '#9DB5C8',      // 冰川蓝（低饱和度）
    primaryLight: '#B8D0E0', // 浅冰川蓝
    primaryDark: '#7A9AB0', // 深冰川蓝

    secondary: '#D4A8B8',    // 火烈鸟红（低饱和度）
    secondaryLight: '#E8C4D0', // 浅火烈鸟红
    secondaryDark: '#B890A0', // 深火烈鸟红

    accent: '#C4B8D0',       // 淡紫色（冰川蓝与火烈鸟红的混合）
    accentLight: '#E0D4E8',

    background: '#F5F7FA',   // 浅蓝灰背景
    surface: '#FAFBFD',     // 卡片背景（偏冷色调）
    surfaceHover: '#F0F4F8',

    text: '#4A5568',         // 深灰蓝文字
    textSecondary: '#6B7280', // 次要文字
    textLight: '#9CA3AF',   // 浅色文字

    border: '#E2E8F0',      // 边框色（偏蓝灰）
    borderLight: '#F1F5F9',

    success: '#9DB5A8',     // 成功色（低饱和度绿蓝）
    warning: '#D4B8A0',     // 警告色（低饱和度橙）
    error: '#D4A0A0',       // 错误色（低饱和度火烈鸟红）
    info: '#9DB5C8',        // 信息色（冰川蓝）
  },

  // 阴影系统 - 弥散阴影（冰川蓝与火烈鸟红）
  shadows: {
    sm: '0 2px 8px rgba(157, 181, 200, 0.08), 0 1px 3px rgba(0, 0, 0, 0.05)',
    md: '0 4px 16px rgba(157, 181, 200, 0.12), 0 2px 6px rgba(0, 0, 0, 0.08)',
    lg: '0 8px 32px rgba(157, 181, 200, 0.15), 0 4px 12px rgba(0, 0, 0, 0.1)',
    xl: '0 12px 48px rgba(157, 181, 200, 0.18), 0 6px 18px rgba(0, 0, 0, 0.12)',

    // 毛玻璃阴影（冰川蓝）
    glass: '0 8px 32px rgba(157, 181, 200, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.6)',
    glassHover: '0 12px 48px rgba(157, 181, 200, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.7)',
  },

  // 毛玻璃效果（冰川蓝调）
  glass: {
    background: 'rgba(255, 255, 255, 0.7)',
    backdropFilter: 'blur(20px) saturate(180%)',
    border: '1px solid rgba(255, 255, 255, 0.5)',
    boxShadow: '0 8px 32px rgba(157, 181, 200, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.6)',
  },

  // 圆角
  borderRadius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    round: '50%',
  },

  // 过渡动画
  transitions: {
    fast: '0.15s ease',
    normal: '0.3s ease',
    slow: '0.5s ease',
    spring: '0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
  },

  // 间距
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
};
