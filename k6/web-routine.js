import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const testType = (__ENV.TEST_TYPE || 'load').toLowerCase();
const flow = (__ENV.FLOW || 'mixed').toLowerCase();

export const options = {
  scenarios: {
    web: {
      executor: 'ramping-vus',
      stages: testType === 'smoke'
        ? [
            { duration: '10s', target: 1 },
            { duration: '20s', target: 1 },
            { duration: '10s', target: 0 },
          ]
        : testType === 'quick'
        ? [
            { duration: '10s', target: 5 },
            { duration: '30s', target: 10 },
            { duration: '20s', target: 20 },
            { duration: '10s', target: 0 },
          ]
        : testType === 'stress'
        ? [
            { duration: '1m', target: 50 },
            { duration: '2m', target: 100 },
            { duration: '2m', target: 200 },
            { duration: '2m', target: 300 },
            { duration: '2m', target: 500 },
            { duration: '1m', target: 0 },
          ]
        : [
            { duration: '1m', target: 10 },
            { duration: '3m', target: 50 },
            { duration: '3m', target: 100 },
            { duration: '1m', target: 0 },
          ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000'],
  },
};

const timings = {
  login: new Trend('flow_login_duration'),
  listGestantes: new Trend('flow_list_gestantes_duration'),
  gestanteDetail: new Trend('flow_gestante_detail_duration'),
  predictionStatus: new Trend('flow_prediction_status_duration'),
  riskSummary: new Trend('flow_risk_summary_duration'),
  createGestante: new Trend('flow_create_gestante_duration'),
  registerAvaliacao: new Trend('flow_register_avaliacao_duration'),
};

const BASE_URL = (__ENV.BASE_URL || 'http://localhost:8001').replace(/\/$/, '');
const USERNAME = __ENV.USERNAME || '12345678901';
const PASSWORD = __ENV.PASSWORD || 'senha12345';
const GESTANTE_ID = __ENV.GESTANTE_ID || '1';
const MUTATING = (__ENV.MUTATING || 'false').toLowerCase() === 'true';
const SLEEP_SECONDS = Number(__ENV.SLEEP_SECONDS || '1');
const LOGIN_EACH_ITERATION = (__ENV.LOGIN_EACH_ITERATION || 'false').toLowerCase() === 'true';
const INCLUDE_RISK_SUMMARY = (__ENV.INCLUDE_RISK_SUMMARY || 'false').toLowerCase() === 'true';

let authenticated = false;

function csrfFrom(response) {
  return response.html().find('input[name=csrfmiddlewaretoken]').first().attr('value');
}

function getWithTiming(url, metric, name, acceptedStatuses = [200]) {
  const response = http.get(url);
  metric.add(response.timings.duration);
  check(response, {
    [`${name} status ok`]: (r) => acceptedStatuses.includes(r.status),
  });
  return response;
}

function login() {
  return group('login', () => {
    const loginPage = http.get(`${BASE_URL}/login/`);
    const csrf = csrfFrom(loginPage);

    check(loginPage, {
      'login page ok': (r) => r.status === 200,
      'login csrf found': () => Boolean(csrf),
    });

    if (!csrf) {
      return false;
    }

    const response = http.post(
      `${BASE_URL}/login/`,
      {
        csrfmiddlewaretoken: csrf,
        nome_login: USERNAME,
        senha: PASSWORD,
      },
      {
        headers: {
          Referer: `${BASE_URL}/login/`,
        },
        redirects: 0,
      },
    );

    timings.login.add(response.timings.duration);
    check(response, {
      'login redirects after success': (r) => r.status === 302,
    });

    return response.status === 302;
  });
}

function listGestantes() {
  group('list gestantes', () => {
    getWithTiming(`${BASE_URL}/`, timings.listGestantes, 'list gestantes');
  });
}

function viewGestanteDetail() {
  group('gestante detail', () => {
    getWithTiming(
      `${BASE_URL}/gestante/${GESTANTE_ID}/`,
      timings.gestanteDetail,
      'gestante detail',
      [200],
    );
  });
}

function predictionStatus() {
  group('prediction status', () => {
    getWithTiming(
      `${BASE_URL}/api-predicao-status/`,
      timings.predictionStatus,
      'prediction status',
    );
  });
}

function riskSummary() {
  group('risk summary', () => {
    getWithTiming(
      `${BASE_URL}/gestantes/${GESTANTE_ID}/resumo/`,
      timings.riskSummary,
      'risk summary',
      [200, 404],
    );
  });
}

function createGestante() {
  group('create gestante', () => {
    const page = http.get(`${BASE_URL}/nova-gestante`);
    const csrf = csrfFrom(page);

    check(page, {
      'create gestante page ok': (r) => r.status === 200,
      'create gestante csrf found': () => Boolean(csrf),
    });

    if (!csrf) {
      return;
    }

    const unique = `${__VU}${__ITER}${Date.now()}`.slice(-8);
    const response = http.post(
      `${BASE_URL}/nova-gestante`,
      {
        csrfmiddlewaretoken: csrf,
        consentimento_aceito: 'true',
        nome: `Gestante K6 ${unique}`,
        telefone: `(98) 9${unique}`,
        data_nascimento: '1995-05-10',
        altura: '1.62',
        peso: '68',
        vulnerabilidade_social: 'False',
      },
      {
        headers: {
          Referer: `${BASE_URL}/nova-gestante`,
        },
        redirects: 0,
      },
    );

    timings.createGestante.add(response.timings.duration);
    check(response, {
      'create gestante accepted': (r) => [200, 302].includes(r.status),
    });
  });
}

function registerAvaliacao() {
  group('register avaliacao', () => {
    const page = http.get(`${BASE_URL}/gestante/${GESTANTE_ID}/cadastrar_questionario/`);
    const csrf = csrfFrom(page);

    check(page, {
      'avaliacao page ok': (r) => r.status === 200,
      'avaliacao csrf found': () => Boolean(csrf),
    });

    if (!csrf) {
      return;
    }

    const payload = {
      csrfmiddlewaretoken: csrf,
    };

    const body = page.body || '';
    const fieldPattern = /<(input|select|textarea)\b[^>]*\bname=["']([^"']+)["'][^>]*>/gi;
    let match;
    while ((match = fieldPattern.exec(body)) !== null) {
      const tag = match[1].toLowerCase();
      const name = match[2];
      const html = match[0];
      const typeMatch = html.match(/\btype=["']([^"']+)["']/i);
      const valueMatch = html.match(/\bvalue=["']([^"']*)["']/i);
      const type = typeMatch ? typeMatch[1].toLowerCase() : tag;

      if (name === 'csrfmiddlewaretoken') {
        continue;
      }
      if (['hidden', 'submit', 'button', 'file'].includes(type)) {
        continue;
      }
      if (type === 'radio' || type === 'checkbox') {
        if (payload[name] === undefined) {
          payload[name] = 'False';
        }
        continue;
      }

      payload[name] = valueMatch ? valueMatch[1] : '1';
    }

    const response = http.post(
      `${BASE_URL}/gestante/${GESTANTE_ID}/cadastrar_questionario/`,
      payload,
      {
        headers: {
          Referer: `${BASE_URL}/gestante/${GESTANTE_ID}/cadastrar_questionario/`,
        },
        redirects: 0,
      },
    );

    timings.registerAvaliacao.add(response.timings.duration);
    check(response, {
      'register avaliacao accepted': (r) => [200, 302].includes(r.status),
    });
  });
}

export default function () {
  const shouldLogin = flow === 'login' || LOGIN_EACH_ITERATION || !authenticated;
  if (shouldLogin) {
    authenticated = login();
  }

  if (!authenticated) {
    sleep(SLEEP_SECONDS);
    return;
  }

  if (flow === 'login') {
    sleep(SLEEP_SECONDS);
    return;
  }

  if (flow === 'list' || flow === 'mixed') {
    listGestantes();
  }

  if (flow === 'detail' || flow === 'mixed') {
    viewGestanteDetail();
    predictionStatus();
    if (INCLUDE_RISK_SUMMARY) {
      riskSummary();
    }
  }

  if (MUTATING && (flow === 'create' || flow === 'mixed')) {
    createGestante();
  }

  if (MUTATING && (flow === 'avaliacao' || flow === 'mixed')) {
    registerAvaliacao();
  }

  sleep(SLEEP_SECONDS);
}
