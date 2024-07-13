import React, { useEffect } from 'react';
import { Button } from 'react-bootstrap';

const SignOut = () => {

    const deleteAllCookies = () => {
        document.cookie.split(';').forEach((c) => {
            document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/');
        });
    };

    const handleSignOutClick = () => {
        const auth2 = window.gapi.auth2.getAuthInstance();
        auth2.signOut().then(() => {
            console.log('User signed out.');
            // Perform additional cleanup or state changes as needed
        }).catch((error) => {
            console.error('Sign out error:', error);
            // Handle sign-out error
        });

        localStorage.removeItem('user_id');
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('user_id');
        sessionStorage.removeItem('access_token');
        deleteAllCookies();
    };

    useEffect(() => {
        const initGapi = () => {
            window.gapi.load('auth2', () => {
                window.gapi.auth2.init({
                    client_id: '461557845801-ihv41ih6s7acp34v00cm6hhr3422qjpc.apps.googleusercontent.com',
                });
            });
        };

        // Load Google API platform.js asynchronously
        const script = document.createElement('script');
        script.src = 'https://apis.google.com/js/platform.js';
        script.async = true;
        script.defer = true;
        script.onload = initGapi;
        document.head.appendChild(script);

        return () => {
            document.head.removeChild(script); // Cleanup: remove script on unmount
        };
    }, []);

    return (
        <Button variant="outline-secondary" onClick={handleSignOutClick}>Sign Out</Button>
    );
};


export default SignOut;