import { createPinia, setActivePinia } from 'pinia';
setActivePinia(createPinia());

import { submitClassroomTraining, getClassroomTrainingDetails } from '../api/training';
import { getToken, setAuth } from '../utils/auth';

// Helper to log to the DOM
function log(msg: string, isError = false) {
    const p = document.createElement('p');
    p.textContent = `[${new Date().toISOString()}] ${msg}`;
    p.style.color = isError ? 'red' : 'green';
    p.style.margin = '2px 0';
    document.getElementById('output')?.appendChild(p);
    console.log(msg);
}

// Ensure tests only run with a valid token
const initializeTestToken = async () => {
    // 假设您已经在开发环境或者有办法获得有效的token。为了真正的端到端测试，
    // 可以替换这里的 TEST_TOKEN 环境变量读取，或手动赋值。
    // 如果没有token，API 会返回401。
    
    // 我们将依赖本地 localStorage 里可能存在的 token（如果在同一个域登录过），
    // 或者你可以硬编码一个测试专用的 token 这里！
    const currentToken = getToken();
    if (!currentToken) {
        log('Warning: No auth token found in localStorage! API requests may fail with 401.', true);
        log('Please log into the main app first on this domain, then run this test page.');
    } else {
        log('Found auth token. Proceeding with tests.');
    }
}

const runTests = async () => {
    try {
        log('=== Starting ClassroomTraining Progress API Tests ===');
        await initializeTestToken();
        
        // 测试参数 (The test parameters corresponding to a BI Training)
        const classroomId = 100;
        const trainingId = 100;
        const studentId = parseInt(localStorage.getItem('userInfo') ? JSON.parse(localStorage.getItem('userInfo')!).id : '3');
        
        log(`Test Parameters: Classroom ${classroomId}, Training ${trainingId}, Student ${studentId}`);
        
        // 1. Submit the training (Simulating a student clicking 'Submit')
        log('1. Submitting classroom training...');
        const submitPayload = { score: 100, completed: true, report: "This is an E2E test submission." };
        const submitResult = await submitClassroomTraining(classroomId, trainingId, studentId, submitPayload);
        
        log(`Submission result: ${JSON.stringify(submitResult)}`);
        if (submitResult.code !== '0000') {
             throw new Error(`Submit failed with code ${submitResult.code}`);
        }
        
        // 2. Fetch the Training Details to verify `student_progress.status === 'completed'`
        log('2. Fetching training details to verify student_progress status...');
        const details = await getClassroomTrainingDetails(classroomId, trainingId, studentId, 'student');
        
        log(`Details retrieved successfully.`);
        
        if (!details.progress) {
            throw new Error('progress object is missing from training details response!');
        }
        
        if (details.progress.status !== 'completed') {
            throw new Error(`Expected progress.status to be 'completed', but got '${details.progress.status}'`);
        }
        
        log('✅ SUCCESS: Progress tracking verified correctly!', false);
        document.getElementById('status')!.textContent = 'Tests Passed ✅';
        document.getElementById('status')!.style.color = 'green';
        
    } catch (e: any) {
        log(`❌ FAILED: ${e.message}`, true);
        if (e.response && e.response.data) {
            log(`Response data: ${JSON.stringify(e.response.data)}`, true);
        }
        document.getElementById('status')!.textContent = 'Tests Failed ❌';
        document.getElementById('status')!.style.color = 'red';
    }
};

// Expose runTests to the global scope for the HTML button
if (typeof window !== 'undefined') {
    (window as any).runTests = runTests;
}

// Auto-run on load
window.addEventListener('load', () => {
    runTests();
});
