// Monaco编辑器延迟加载器
let monacoPromise: Promise<typeof import('monaco-editor')> | null = null;

export async function loadMonaco() {
  if (!monacoPromise) {
    monacoPromise = import('monaco-editor').then(async (monaco) => {
      // 动态导入workers
      const [editorWorker, jsonWorker, cssWorker, htmlWorker, tsWorker] = await Promise.all([
        import('monaco-editor/esm/vs/editor/editor.worker?worker'),
        import('monaco-editor/esm/vs/language/json/json.worker?worker'),
        import('monaco-editor/esm/vs/language/css/css.worker?worker'),
        import('monaco-editor/esm/vs/language/html/html.worker?worker'),
        import('monaco-editor/esm/vs/language/typescript/ts.worker?worker')
      ]);

      // 配置Monaco环境
      if (typeof window !== 'undefined') {
        (window as any).MonacoEnvironment = {
          getWorker(_: any, label: string) {
            if (label === 'json') {
              return new jsonWorker.default();
            }
            if (label === 'css' || label === 'scss' || label === 'less') {
              return new cssWorker.default();
            }
            if (label === 'html' || label === 'handlebars' || label === 'razor') {
              return new htmlWorker.default();
            }
            if (label === 'typescript' || label === 'javascript') {
              return new tsWorker.default();
            }
            return new editorWorker.default();
          }
        };
      }

      return monaco;
    });
  }
  
  return monacoPromise;
}