angular.module('application', ['active-ng']).
    factory('httpDefaultCache', function($cacheFactory) {
        return $cacheFactory('httpDefaultCache', {
            capacity: 10
        });
    }).
    service('MyAuthService', function($http, $location){
//        var MyAuthServiceObj = this;
//
//        this.authenticated = false; // this is a boolean that will be modified by the following methods:
//        $http({
//            method: 'GET',
//            url: '/api/checkAuth'
//        }).success(function(data, status, headers, config) {
//            if (parseInt(data) === 1) {
//                MyAuthServiceObj.authenticated = true;
//            } else {
//                $location.path('/login');
//            }
//        });
//
////        MyAuthServiceObj.userinfo = undefined;
//
//        this.getUserinfo = function(field){
//            if (MyAuthServiceObj.userinfo === undefined) {
//                $http({
//                    method: 'GET',
//                    url: '/api/whoami'
//                }).success(function(data, status, headers, config) {
//                    MyAuthServiceObj.userinfo = data;
//                    });
//            }
//            return MyAuthServiceObj.userinfo !== undefined ? MyAuthServiceObj.userinfo[field] : '';
//        };
//
//        // I supose that you have methods similar to these ones
//        this.login = function(username, password){
//            var result = false;
//            $http({
//                method: 'POST',
//                data: $.param({
//                    'LoginForm[username]': username,
//                    'LoginForm[password]': password
//                }),
//                url: '/api/login',
//                headers: {'Content-Type': 'application/x-www-form-urlencoded'}
//            }).success(function(data, status, headers, config) {
//                if (parseInt(data) === 1) {
//                    MyAuthServiceObj.authenticated = true;
//                    $location.path('/');
//                }
//            });
//            return result;
//        };
//
//        this.logout = function(){
//            $http({
//                method: 'GET',
//                url: '/api/logout'
//            }).success(function(data, status, headers, config) {
//                if (parseInt(data) === 1) {
//                    MyAuthServiceObj.authenticated = false;
//                }
//            });
//        }

    }).
    config(['$routeProvider', '$locationProvider', function ($routeProvider, $locationProvider) {
        $routeProvider.
            when('/', {
                templateUrl: '/static/app/views/monitoring/index.html',
                controller: DashboardCtrl
            }).
            when('/hosts', {
                templateUrl: '/static/app/views/hosts/index.html',
                controller: HostsCtrl
            }).
            when('/hosts/add', {
                templateUrl: '/static/app/views/hosts/add.html',
                controller: HostAddCtrl
            }).
            when('/hosts/delete/:server_name', {
                templateUrl: '/static/app/views/hosts/delete.html',
                controller: HostDeleteCtrl
            }).
            when('/services', {
                templateUrl: '/static/app/views/services/index.html',
                controller: ServicesCtrl
            }).
            when('/help', {
                templateUrl: '/static/app/views/help/index.html',
                controller: EmptyCtrl
            }).
            when('/logs/nginx/:logtype', {
                templateUrl: '/static/app/views/logs/index.html',
                controller: LogNginxCtrl
            });
        $locationProvider.html5Mode(true);
    }]);