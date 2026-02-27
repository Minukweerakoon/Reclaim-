import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
    apiKey: 'AIzaSyBNeIFLwA2ARw7_4yjBnmuqTsXpoAsnmFg',
    authDomain: 'lost-and-found-74f4d.firebaseapp.com',
    projectId: 'lost-and-found-74f4d',
    storageBucket: 'lost-and-found-74f4d.firebasestorage.app',
    messagingSenderId: '453133053243',
    appId: '1:453133053243:web:67d936bbfacd5d93e21b1e',
    measurementId: 'G-2BT0P47ZYS',
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
