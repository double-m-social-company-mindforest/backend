# 프론트엔드 쿠키 인증 수정 가이드

새로고침 시 쿠키가 사라지는 문제를 해결하기 위한 프론트엔드 코드 수정 사항입니다.

## 문제점
- localStorage에 토큰을 저장하면서 동시에 백엔드에서 쿠키도 설정
- api 설정에 `withCredentials: true` 누락으로 쿠키 전송 안됨
- 새로고침 시 쿠키는 유지되지만 localStorage만 확인하여 인증 실패

## 해결책

### 1. util/api.js 파일 수정

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
    withCredentials: true,  // 🔥 쿠키 전송을 위해 필수!
    headers: {
        'Content-Type': 'application/json',
    }
});

// 응답 인터셉터: 401 에러 시 로그아웃 처리
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // 인증 실패 시 로그인 페이지로 리다이렉트
            window.location.href = '/admin';
        }
        return Promise.reject(error);
    }
);

export default api;
```

### 2. Signin 컴포넌트의 handleSubmit 함수 수정

**기존 코드:**
```javascript
const handleSubmit = async () => {
    try {
        const url =
            role === "admin"
                ? "/api/v1/admin/auth/login"
                : "/api/v1/counselors/auth/login";

        const response = await api.post(url, form);
        const token = response.data.access_token;

        localStorage.setItem(role === "admin" ? "token" : "access_token", token);

        navigate(role === "admin" ? "/admin/dashboard" : "/dashboard");
    } catch (error: any) {
        // 에러 처리...
    }
};
```

**수정된 코드:**
```javascript
const handleSubmit = async () => {
    try {
        const url =
            role === "admin"
                ? "/api/v1/admin/auth/login"
                : "/api/v1/counselors/auth/login";

        const response = await api.post(url, form);
        
        navigate(role === "admin" ? "/admin/dashboard" : "/dashboard");
    } catch (error: any) {
        if (
            role === "counselor" &&
            error.response?.status === 403 &&
            error.response.data?.detail === "관리자 승인이 필요한 계정입니다"
        ) {
            setIsPending(true);
        } else {
            alert("로그인에 실패했습니다.");
            console.error("로그인 오류:", error.response?.data || error.message);
        }
    }
};
```

### 3. Input 컴포넌트에 autoComplete 속성 추가

**아이디 입력 필드:**
```javascript
<Input 
    name="username" 
    value={form.username} 
    onChange={handleChange}
    autoComplete="username"  // 추가
/>
```

**비밀번호 입력 필드:**
```javascript
<Input
    name="password"
    type="password"
    value={form.password}
    onChange={handleChange}
    autoComplete="current-password"  // 추가
/>
```

### 4. 버튼 hover 효과 추가 (선택사항)

```javascript
const LoginButton = styled.button`
    background: white;
    color: #333;
    border: 1px solid #ccc;
    border-radius: 12px;
    padding: 10px 20px;
    cursor: pointer;
    
    &:hover {
        background: #f5f5f5;
    }
`;

const FindButton = styled.button`
    background: white;
    color: #333;
    border: 1px solid #ccc;
    border-radius: 12px;
    padding: 10px 20px;
    cursor: pointer;
    
    &:hover {
        background: #f5f5f5;
    }
`;
```

## 추가 권장사항

### 1. 인증 상태 확인 Hook 생성 (hooks/useAuth.js)

```javascript
import { useState, useEffect } from 'react';
import api from '../util/api';

export const useAuth = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        try {
            // 관리자 인증 상태 확인
            const response = await api.get('/api/v1/admin/auth/me');
            setIsAuthenticated(true);
            setUser(response.data);
        } catch (error) {
            // 상담사 인증 상태 확인
            try {
                const response = await api.get('/api/v1/counselors/auth/me');
                setIsAuthenticated(true);
                setUser(response.data);
            } catch (counselorError) {
                setIsAuthenticated(false);
                setUser(null);
            }
        } finally {
            setLoading(false);
        }
    };

    const logout = async () => {
        try {
            await api.post('/api/v1/admin/auth/logout');
        } catch (error) {
            // 로그아웃 실패해도 계속 진행
        } finally {
            setIsAuthenticated(false);
            setUser(null);
            window.location.href = '/admin';
        }
    };

    return { isAuthenticated, user, loading, checkAuthStatus, logout };
};
```

### 2. Dashboard 컴포넌트에서 사용 예시

```javascript
import { useAuth } from '../hooks/useAuth';

const Dashboard = () => {
    const { isAuthenticated, user, loading, logout } = useAuth();

    if (loading) {
        return <div>로딩중...</div>;
    }

    if (!isAuthenticated) {
        return <div>로그인이 필요합니다.</div>;
    }

    return (
        <div>
            <h1>안녕하세요, {user?.name}님!</h1>
            <button onClick={logout}>로그아웃</button>
        </div>
    );
};
```

## 수정 후 예상 동작

1. ✅ **로그인**: 쿠키가 자동으로 설정됨
2. ✅ **새로고침**: 쿠키가 유지되어 인증 상태 지속
3. ✅ **API 호출**: 쿠키가 자동으로 전송됨
4. ✅ **로그아웃**: 쿠키가 삭제됨
5. ✅ **401 오류**: 자동으로 로그인 페이지로 리다이렉트

## 중요 포인트

- **withCredentials: true** 설정이 가장 중요합니다
- localStorage 저장을 제거하고 쿠키만 사용합니다
- httpOnly 쿠키는 JavaScript로 읽을 수 없으므로 API 호출로 인증 상태를 확인합니다

이 수정사항을 적용하면 새로고침해도 로그인 상태가 유지됩니다!