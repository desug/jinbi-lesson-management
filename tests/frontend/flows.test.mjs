import test from 'node:test';
import assert from 'node:assert/strict';
import { createFrontend } from './loader.mjs';

test('Mock student login preserves profile and auth state through the public API', async () => {
  const env = await createFrontend();
  (await env.import('config')).default.useMock = true;
  const database = (await env.import('mock/database')).getDatabase();
  const result = await (await env.import('api/auth')).studentLogin(database.students[0].phone);
  assert.equal(result.data.student.id, database.students[0].id);
  assert.equal(result.data.student.name, database.students[0].name);
  assert.ok(result.data.student.subjects[0].remainingHours > 0);
  assert.equal(env.uni.getStorageSync('userType'), 'student');
  assert.ok(env.uni.getStorageSync('token'));
  assert.equal(env.requests.length, 0);
});

test('Mock admin login, list and adjustment run without a backend', async () => {
  const env = await createFrontend();
  (await env.import('config')).default.useMock = true;
  const database = (await env.import('mock/database')).getDatabase();
  const auth = await env.import('api/auth');
  const login = await auth.adminLogin(database.admins[0].account, database.admins[0].password);
  assert.equal(login.data.admin.username, database.admins[0].account);
  const api = await env.import('api/admin');
  const list = await api.getAdminStudents();
  assert.ok(list.data.list.length > 0);
  const student = database.students[0];
  const subject = student.subjects[0];
  await api.changeLesson({ studentId: student.id, subjectName: subject.subjectName,
                           changeType: 'add', hours: 2, amount: 0 });
  const latest = (await env.import('mock/database')).getStudentById(student.id);
  assert.equal(latest.subjects[0].remainingHours, subject.remainingHours + 2);
  assert.equal(env.requests.length, 0);
});

test('Request adds Bearer token, encodes GET parameters and normalizes response', async () => {
  const env = await createFrontend();
  env.uni.setStorageSync('token', 'test-token');
  env.respond(options => {
    assert.equal(options.header.Authorization, 'Bearer test-token');
    assert.ok(options.url.includes('keyword=%E6%BC%94%E7%A4%BA'));
    options.success({ statusCode: 200, data: { student_id: 7, total_hours: 10 } });
  });
  const request = (await env.import('utils/request')).default;
  const response = await request({ url: '/admin/students', data: { keyword: '演示' } });
  assert.equal(response.data.studentId, 7);
  assert.equal(response.data.totalHours, 10);
});

test('Request rejects HTTP 200 business errors and clears auth on 401', async () => {
  const env = await createFrontend();
  const request = (await env.import('utils/request')).default;
  env.respond(options => options.success({ statusCode: 200,
    data: { success: false, code: 'INSUFFICIENT_HOURS', message: '课时不足' } }));
  await assert.rejects(request({ url: '/admin/lesson/change', method: 'POST' }),
                       error => error.code === 'INSUFFICIENT_HOURS');
  env.uni.setStorageSync('token', 'expired-token');
  env.respond(options => options.success({ statusCode: 401, data: { message: '未登录' } }));
  await assert.rejects(request({ url: '/student/profile' }));
  assert.equal(env.uni.getStorageSync('token'), '');
});

test('Log redaction preserves original data and hides nested credentials', async () => {
  const env = await createFrontend();
  const original = { password: 'private', nested: { token: 'private-token', value: 1 } };
  const sanitized = (await env.import('utils/request')).sanitizeRequestData(original);
  assert.equal(sanitized.password, '***');
  assert.equal(sanitized.nested.token, '***');
  assert.equal(original.password, 'private');
  assert.equal(original.nested.token, 'private-token');
});

test('Mock rejects excessive deduction without changing balance or records', async () => {
  const env = await createFrontend();
  const db = await env.import('mock/database');
  const student = db.getDatabase().students[0];
  const result = db.updateStudentHours({ studentId: student.id, subject: student.subjects[0].subjectName,
    changeType: '扣减', hours: student.subjects[0].remainingHours + 1 });
  assert.notEqual(result.code, 0);
  const after = db.getStudentById(student.id);
  assert.equal(after.subjects[0].remainingHours, student.subjects[0].remainingHours);
  assert.equal(after.records.length, student.records.length);
});
