// 配置Vue使用自定义分隔符，避免与Flask的Jinja2模板引擎冲突
Vue.options.delimiters = ['[[', ']]'];

// 创建Vue实例
new Vue({
    el: '#app',
    data: {
        // 认证相关
        isLoggedIn: false,
        user: {},
        token: '',
        loginForm: {
            username: '',
            password: ''
        },
        loginError: null,
        // 注册相关
        showRegisterForm: false,
        registerForm: {
            username: '',
            email: '',
            password: '',
            confirmPassword: ''
        },
        registerError: null,
        registerSuccess: null,
        
        // 视图控制
        currentView: 'monitor',
        
        // 监测信息相关
        monitorPoints: [],
        monitorRecords: [],
        
        // 新增监测点表单
        newMonitorPoint: {
            name: '',
            latitude: 35.0,
            longitude: 116.0
        },
        
        // 新增监测记录表单
        newMonitorRecord: {
            monitor_point_id: '',
            wind_speed: 10.0,
            temperature: 25.0,
            humidity: 60.0
        },
        
        // 火灾预测相关
        firePredictions: [],
        customPredictionForm: {
            wind_speed: 10,
            temperature: 30,
            humidity: 60
        },
        customPredictionResult: null,
        
        // 阈值设置
        thresholdForm: {
            wind_speed_threshold: 10.0,
            temperature_threshold: 30.0,
            humidity_threshold: 30.0
        },
        
        // 统计数据
        fireRiskStats: {},
        summary: {
            monitor_points_count: 0,
            total_fire_records: 0,
            high_risk_areas_last_week: 0,
            avg_fire_area: 0
        },
        recentFires: [],
        
        // 用户管理
        users: [],
        newUser: {
            username: '',
            email: '',
            password: '',
            role: 'user'
        },
        editingUser: {
            id: null,
            username: '',
            email: '',
            password: '',
            role: ''
        },
        
        // 模态框控制
        showAddUserModal: false,
        showEditUserModal: false,
        showAddMonitorPointModal: false,
        showAddMonitorRecordModal: false
    },
    
    created() {
        // 检查本地存储中是否有令牌
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('user');
        
        if (token && userData) {
            this.token = token;
            this.user = JSON.parse(userData);
            this.isLoggedIn = true;
            
            // 设置axios默认头
            axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
        }
        
        // 不管是否登录，都加载初始数据
        this.loadInitialData();
    },
    
    mounted() {
        // 确保jQuery和Bootstrap已正确加载
        if (typeof $ !== 'undefined' && typeof $.fn.modal !== 'undefined') {
            // 初始化所有模态框
            $('#addUserModal').on('hidden.bs.modal', () => {
                this.showAddUserModal = false;
            });
            
            $('#editUserModal').on('hidden.bs.modal', () => {
                this.showEditUserModal = false;
            });
            
            $('#addMonitorPointModal').on('hidden.bs.modal', () => {
                this.showAddMonitorPointModal = false;
            });
            
            $('#addMonitorRecordModal').on('hidden.bs.modal', () => {
                this.showAddMonitorRecordModal = false;
            });
        } else {
            console.warn('jQuery或Bootstrap模态框未正确加载');
        }
    },
    
    methods: {
        // 认证相关方法
        async login() {
            try {
                this.loginError = null;
                const response = await axios.post('/api/auth/login', this.loginForm);
                
                this.token = response.data.access_token;
                this.user = response.data.user;
                this.isLoggedIn = true;
                
                // 保存到本地存储
                localStorage.setItem('token', this.token);
                localStorage.setItem('user', JSON.stringify(this.user));
                
                // 设置axios默认头
                axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
                
                // 加载初始数据
                this.loadInitialData();
                
                // 重置登录表单
                this.loginForm = { username: '', password: '' };
            } catch (error) {
                console.error('登录失败:', error);
                this.loginError = error.response?.data?.message || '登录失败，请检查用户名和密码';
            }
        },
        
        async register() {
            try {
                this.registerError = null;
                this.registerSuccess = null;
                
                // 检查密码是否匹配
                if (this.registerForm.password !== this.registerForm.confirmPassword) {
                    this.registerError = '两次输入的密码不一致';
                    return;
                }
                
                // 发送注册请求
                const response = await axios.post('/api/auth/register', {
                    username: this.registerForm.username,
                    email: this.registerForm.email,
                    password: this.registerForm.password
                });
                
                // 显示成功消息
                this.registerSuccess = '注册成功，请登录';
                
                // 重置注册表单
                this.registerForm = { username: '', email: '', password: '', confirmPassword: '' };
                
                // 3秒后自动切换到登录页
                setTimeout(() => {
                    this.showRegisterForm = false;
                    this.registerSuccess = null;
                }, 3000);
                
            } catch (error) {
                console.error('注册失败:', error);
                this.registerError = error.response?.data?.message || '注册失败，请稍后再试';
            }
        },
        
        logout() {
            this.isLoggedIn = false;
            this.user = {};
            this.token = '';
            
            // 清除本地存储
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            
            // 清除axios默认头
            delete axios.defaults.headers.common['Authorization'];
            
            // 重置当前视图
            this.currentView = 'monitor';
        },
        
        // 数据加载方法
        async loadInitialData() {
            // 根据当前视图加载相应数据
            try {
                switch (this.currentView) {
                    case 'monitor':
                        await this.loadMonitorData();
                        break;
                    case 'prediction':
                        await this.loadPredictionData();
                        break;
                    case 'fireSettings':
                        await this.loadThresholdData();
                        break;
                    case 'stats':
                        await this.loadStatData();
                        break;
                    case 'users':
                        if (this.isLoggedIn && this.user.role === 'admin') {
                            await this.loadUserData();
                        }
                        break;
                }
            } catch (error) {
                console.error('数据加载失败:', error);
                // 不显示错误提示，只在控制台记录
            }
        },
        
        // 监测数据相关方法
        async loadMonitorData() {
            try {
                // 加载监测点
                const pointsResponse = await axios.get('/api/monitor/points');
                this.monitorPoints = pointsResponse.data;
                
                // 加载最新监测记录
                const recordsResponse = await axios.get('/api/monitor/latest');
                this.monitorRecords = recordsResponse.data;
            } catch (error) {
                console.error('加载监测数据失败:', error);
                alert('加载监测数据失败');
            }
        },
        
        // 火灾预测相关方法
        async loadPredictionData() {
            try {
                const response = await axios.get('/api/fire/predict');
                this.firePredictions = response.data;
            } catch (error) {
                console.error('加载预测数据失败:', error);
                alert('加载预测数据失败');
            }
        },
        
        async calculateCustomPrediction() {
            try {
                // 确保提交的是数值类型
                const customData = {
                    wind_speed: parseFloat(this.customPredictionForm.wind_speed) || 10,
                    temperature: parseFloat(this.customPredictionForm.temperature) || 30,
                    humidity: parseFloat(this.customPredictionForm.humidity) || 60
                };
                
                // 验证数值范围有效性
                if (customData.wind_speed < 0 || customData.wind_speed > 100) {
                    customData.wind_speed = 10;
                }
                
                if (customData.temperature < -50 || customData.temperature > 100) {
                    customData.temperature = 30;
                }
                
                if (customData.humidity < 0 || customData.humidity > 100) {
                    customData.humidity = 60;
                }
                
                console.log("发送预测请求数据:", JSON.stringify(customData));
                const response = await axios.post('/api/fire/predict/custom', customData);
                console.log("接收预测响应数据:", JSON.stringify(response.data));
                
                if (response.data && response.data.risk_level) {
                    this.customPredictionResult = response.data;
                } else {
                    this.customPredictionResult = {
                        risk_level: 'medium',
                        predicted_area: 0.5,
                        wind_speed: customData.wind_speed,
                        temperature: customData.temperature,
                        humidity: customData.humidity
                    };
                }
            } catch (error) {
                console.error('自定义预测失败:', error);
                // 出错时设置默认结果
                this.customPredictionResult = {
                    risk_level: 'medium',
                    predicted_area: 0.5,
                    wind_speed: parseFloat(this.customPredictionForm.wind_speed) || 10,
                    temperature: parseFloat(this.customPredictionForm.temperature) || 30,
                    humidity: parseFloat(this.customPredictionForm.humidity) || 60
                };
                
                alert('自定义预测处理遇到问题，已显示默认结果');
            }
        },
        
        async savePrediction(prediction) {
            try {
                // 确保预测数据包含必要字段
                const dataToSave = {
                    wind_speed: prediction.wind_speed,
                    temperature: prediction.temperature,
                    humidity: prediction.humidity,
                    risk_level: prediction.risk_level,
                    predicted_area: prediction.predicted_area
                };
                
                // 如果有监测点ID，则添加
                if (prediction.monitor_point_id) {
                    dataToSave.monitor_point_id = prediction.monitor_point_id;
                }
                
                // 如果有经纬度，则添加
                if (prediction.latitude) dataToSave.latitude = prediction.latitude;
                if (prediction.longitude) dataToSave.longitude = prediction.longitude;
                
                await axios.post('/api/fire/save-prediction', dataToSave);
                alert('预测数据保存成功');
            } catch (error) {
                console.error('保存预测数据失败:', error);
                alert('保存预测数据失败');
            }
        },
        
        // 阈值设置相关方法
        async loadThresholdData() {
            try {
                const response = await axios.get('/api/fire/threshold');
                this.thresholdForm = response.data;
            } catch (error) {
                console.error('加载阈值设置失败:', error);
                alert('加载阈值设置失败');
            }
        },
        
        async updateThresholds() {
            try {
                // 确保提交的是数值类型
                const thresholdData = {
                    wind_speed_threshold: parseFloat(this.thresholdForm.wind_speed_threshold) || 10.0,
                    temperature_threshold: parseFloat(this.thresholdForm.temperature_threshold) || 30.0,
                    humidity_threshold: parseFloat(this.thresholdForm.humidity_threshold) || 30.0
                };
                
                // 验证数值范围有效性
                if (thresholdData.wind_speed_threshold <= 0 || thresholdData.wind_speed_threshold > 100) {
                    thresholdData.wind_speed_threshold = 10.0;
                }
                
                if (thresholdData.temperature_threshold <= 0 || thresholdData.temperature_threshold > 100) {
                    thresholdData.temperature_threshold = 30.0;
                }
                
                if (thresholdData.humidity_threshold <= 0 || thresholdData.humidity_threshold >= 100) {
                    thresholdData.humidity_threshold = 30.0;
                }
                
                await axios.post('/api/fire/threshold', thresholdData);
                
                // 更新本地表单数据
                this.thresholdForm = { ...thresholdData };
                
                alert('阈值设置更新成功');
            } catch (error) {
                console.error('更新阈值设置失败:', error);
                alert('更新阈值设置失败');
            }
        },
        
        // 统计数据相关方法
        async loadStatData() {
            try {
                // 加载火灾风险统计
                const riskResponse = await axios.get('/api/stats/fire-count');
                if (riskResponse.data && riskResponse.data.by_risk) {
                    this.fireRiskStats = riskResponse.data.by_risk;
                } else {
                    this.fireRiskStats = {};
                }
                
                // 加载系统概要
                const summaryResponse = await axios.get('/api/stats/summary');
                if (summaryResponse.data) {
                    this.summary = summaryResponse.data;
                    this.recentFires = summaryResponse.data.recent_fires || [];
                }
            } catch (error) {
                console.error('加载统计数据失败:', error);
                // 使用默认数据
                this.fireRiskStats = {};
                this.summary = {
                    monitor_points_count: 0,
                    total_fire_records: 0,
                    high_risk_areas_last_week: 0,
                    avg_fire_area: 0
                };
                this.recentFires = [];
            }
        },
        
        // 用户管理相关方法
        async loadUserData() {
            if (!this.isLoggedIn) {
                console.warn('用户未登录，无法加载用户数据');
                this.users = [];
                return;
            }
            
            try {
                const response = await axios.get('/api/users/');
                this.users = response.data;
            } catch (error) {
                console.error('加载用户数据失败:', error);
                // 不显示错误提示，只在控制台记录
                this.users = [];
            }
        },
        
        async addUser() {
            try {
                await axios.post('/api/users/', this.newUser);
                alert('用户添加成功');
                
                // 重置表单
                this.newUser = {
                    username: '',
                    email: '',
                    password: '',
                    role: 'user'
                };
                
                // 关闭模态框
                this.showAddUserModal = false;
                
                // 重新加载用户数据
                await this.loadUserData();
                
                // 初始化模态框
                $('#addUserModal').modal('hide');
            } catch (error) {
                console.error('添加用户失败:', error);
                alert('添加用户失败: ' + (error.response?.data?.message || '未知错误'));
            }
        },
        
        editUser(user) {
            // 复制用户数据到编辑表单
            this.editingUser = {
                id: user.id,
                username: user.username,
                email: user.email,
                password: '', // 密码留空
                role: user.role
            };
            
            // 显示编辑模态框
            this.showEditUserModal = true;
            $('#editUserModal').modal('show');
        },
        
        async updateUser() {
            try {
                // 构建更新数据
                const updateData = {
                    username: this.editingUser.username,
                    email: this.editingUser.email
                };
                
                // 如果密码不为空，则更新密码
                if (this.editingUser.password) {
                    updateData.password = this.editingUser.password;
                }
                
                await axios.put(`/api/users/${this.editingUser.id}`, updateData);
                alert('用户更新成功');
                
                // 关闭模态框
                this.showEditUserModal = false;
                
                // 重新加载用户数据
                await this.loadUserData();
                
                // 初始化模态框
                $('#editUserModal').modal('hide');
            } catch (error) {
                console.error('更新用户失败:', error);
                alert('更新用户失败: ' + (error.response?.data?.message || '未知错误'));
            }
        },
        
        async setAdmin(userId) {
            try {
                await axios.put(`/api/users/set-admin/${userId}`);
                alert('设置管理员成功');
                await this.loadUserData();
            } catch (error) {
                console.error('设置管理员失败:', error);
                alert('设置管理员失败');
            }
        },
        
        async removeAdmin(userId) {
            try {
                await axios.put(`/api/users/remove-admin/${userId}`);
                alert('移除管理员权限成功');
                await this.loadUserData();
            } catch (error) {
                console.error('移除管理员权限失败:', error);
                alert('移除管理员权限失败');
            }
        },
        
        async deleteUser(userId) {
            if (!confirm('确定要删除此用户吗？')) return;
            
            try {
                await axios.delete(`/api/users/${userId}`);
                alert('用户删除成功');
                await this.loadUserData();
            } catch (error) {
                console.error('删除用户失败:', error);
                alert('删除用户失败');
            }
        },
        
        // 监测点相关方法
        async addMonitorPoint() {
            try {
                await axios.post('/api/monitor/points', this.newMonitorPoint);
                alert('监测点添加成功');
                
                // 重置表单
                this.newMonitorPoint = {
                    name: '',
                    latitude: 35.0,
                    longitude: 116.0
                };
                
                // 关闭模态框
                this.showAddMonitorPointModal = false;
                $('#addMonitorPointModal').modal('hide');
                
                // 重新加载监测点数据
                await this.loadMonitorData();
            } catch (error) {
                console.error('添加监测点失败:', error);
                alert('添加监测点失败: ' + (error.response?.data?.message || '未知错误'));
            }
        },
        
        async addMonitorRecord() {
            if (!this.isLoggedIn) {
                alert('请先登录后再进行此操作');
                return;
            }
            
            try {
                await axios.post('/api/monitor/records', this.newMonitorRecord);
                alert('监测记录添加成功');
                
                // 重置表单，但保留监测点选择
                const pointId = this.newMonitorRecord.monitor_point_id;
                this.newMonitorRecord = {
                    monitor_point_id: pointId,
                    wind_speed: 10.0,
                    temperature: 25.0,
                    humidity: 60.0
                };
                
                // 关闭模态框
                this.showAddMonitorRecordModal = false;
                $('#addMonitorRecordModal').modal('hide');
                
                // 重新加载监测数据
                await this.loadMonitorData();
                
                // 如果当前在预测页面，也重新加载预测数据
                if (this.currentView === 'prediction') {
                    await this.loadPredictionData();
                }
            } catch (error) {
                console.error('添加监测记录失败:', error);
                alert('添加监测记录失败: ' + (error.response?.data?.message || '未知错误'));
            }
        },
        
        viewMonitorDetail(record) {
            alert(`监测点: ${record.monitor_point_name}\n时间: ${record.timestamp}\n风速: ${record.wind_speed} m/s\n温度: ${record.temperature} °C\n湿度: ${record.humidity} %\n经度: ${record.longitude}\n纬度: ${record.latitude}`);
        },
        
        async deleteMonitorRecord(recordId) {
            if (!this.isLoggedIn || this.user.role !== 'admin') {
                alert('只有管理员才能删除监测记录');
                return;
            }
            
            if (!confirm('确定要删除此监测记录吗？')) return;
            
            try {
                await axios.delete(`/api/monitor/records/${recordId}`);
                alert('监测记录删除成功');
                await this.loadMonitorData();
            } catch (error) {
                console.error('删除监测记录失败:', error);
                alert('删除监测记录失败');
            }
        },
        
        // 工具方法
        getRiskText(level) {
            const riskTextMap = {
                'low': '低风险',
                'medium': '中风险',
                'high': '高风险',
                'extreme': '极高风险'
            };
            return riskTextMap[level] || level;
        },
        
        getRiskClass(level) {
            return `risk-${level}`;
        },
        
        getRiskAlertClass(level) {
            const alertClassMap = {
                'low': 'alert-success',
                'medium': 'alert-warning',
                'high': 'alert-danger',
                'extreme': 'alert-dark'
            };
            return alertClassMap[level] || 'alert-info';
        },
        
        // 打开模态框的方法
        openAddMonitorPointModal() {
            this.showAddMonitorPointModal = true;
            this.$nextTick(() => {
                // 使用jQuery显示模态框
                $('#addMonitorPointModal').modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                });
            });
        },
        
        openAddMonitorRecordModal() {
            this.showAddMonitorRecordModal = true;
            this.$nextTick(() => {
                // 使用jQuery显示模态框
                $('#addMonitorRecordModal').modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                });
            });
        },
        
        openAddUserModal() {
            this.showAddUserModal = true;
            this.$nextTick(() => {
                // 使用jQuery显示模态框
                $('#addUserModal').modal({
                    backdrop: 'static',
                    keyboard: false,
                    show: true
                });
            });
        },
    },
    
    watch: {
        // 监听视图变化，加载相应数据
        currentView(newView) {
            switch (newView) {
                case 'monitor':
                    this.loadMonitorData();
                    break;
                case 'prediction':
                    this.loadPredictionData();
                    break;
                case 'fireSettings':
                    this.loadThresholdData();
                    break;
                case 'stats':
                    this.loadStatData();
                    break;
                case 'users':
                    if (this.user.role === 'admin') {
                        this.loadUserData();
                    }
                    break;
            }
        }
    }
}); 