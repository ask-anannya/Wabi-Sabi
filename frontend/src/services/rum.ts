import { datadogRum } from "@datadog/browser-rum";

export const initDatadogRUM = () => {
  datadogRum.init({
    applicationId: import.meta.env.VITE_DD_APPLICATION_ID,
    clientToken: import.meta.env.VITE_DD_CLIENT_TOKEN,
    site: import.meta.env.VITE_DD_SITE,

    service: import.meta.env.VITE_DD_SERVICE,
    env: import.meta.env.VITE_DD_ENV,
    version: "1.0.0",

    sessionSampleRate: 100,
    sessionReplaySampleRate: 100,

    trackUserInteractions: true,
    trackResources: true,
    trackLongTasks: true,

    defaultPrivacyLevel: "mask-user-input",

    allowedTracingUrls: [
      /http:\/\/localhost:8000/,
      /https:\/\/your-backend-domain/,
    ],
  });
};
