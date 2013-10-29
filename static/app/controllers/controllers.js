function DashboardCtrl($scope) {

}

function HostsCtrl($scope, $http) {
    $scope.hosts = [];

    $http({
        method: 'GET',
        url: '/api/get_hosts'
    }).
        success(function(data, status, headers, config) {
            $scope.hosts = data;
        }).
        error(function(data, status, headers, config) {
        });

}

function EmptyCtrl($scope) {

}

function ServicesCtrl($scope, $http) {
    $scope.output = '';

    $scope.restartNginx = function() {
        $http({
        method: 'GET',
        url: '/api/restart/nginx'
    }).
        success(function(data, status, headers, config) {
            $scope.output = data['output'];
        }).
        error(function(data, status, headers, config) {
        });
    }


    $scope.restartPhpFpm = function() {
        $http({
        method: 'GET',
        url: '/api/restart/php-fpm'
    }).
        success(function(data, status, headers, config) {
            $scope.output = data['output'];
        }).
        error(function(data, status, headers, config) {
        });
    }
}

function LogNginxCtrl($scope, $http, $routeParams) {
    $scope.log = '';

    $http({
        method: 'GET',
        url: '/api/get_log/nginx/'+$routeParams.logtype
    }).
        success(function(data, status, headers, config) {
            $scope.log = data['log'];
        }).
        error(function(data, status, headers, config) {
        });
}

function MainMenuCtrl($scope) {
    $scope.main_menu = [
        {"url": "/", "title": "Мониторинг"},
        {"url": "/services", "title": "Сервисы"},
        {"url": "/hosts", "title": "Хосты"},
        {"url": "/logs", "title": "Логи"},
        {"url": "/help", "title": "Помощь"}
    ];
}

function LeftMenuCtrl($scope) {
    $scope.$on("$locationChangeStart", function (event, next, current) {
        var reg = /.+?\:\/\/.+?(\/.+?)(?:#|\?|$|\/)/i;
        var pathname = reg.exec(next);
        if (pathname === null) {
            pathname = '/';
        } else {
            pathname = pathname[1];
        }

        var left_menu_includes = {
            "/": [
                {"url": "/", "title": "Дашборд"}
            ],
            "/services": [
                {"url": "/services", "title": "Сервисы"},
            ],
            "/hosts": [
                {"url": "/hosts", "title": "Хосты"},
                {"url": "/hosts/add", "title": "Добавить хост"}
            ],
            "/logs": [
                {"url": "/logs/nginx/access", "title": "Nginx Access Log"},
                {"url": "/logs/nginx/error", "title": "Nginx Error Log"}
            ],
            "/help": [
                {"url": "/help", "title": "Помощь"}
            ]
        };

        $scope.left_menu = left_menu_includes[pathname];
    });
}

function HostAddCtrl($scope, $http, $location) {
    // references
    $scope.engines = [
        {id: 'none', title: 'Отсутствует'},
        {id: 'joomla', title: 'Joomla'}
    ];
    // default
    $scope.user = 'www-data';
    $scope.server_name = 'example.local';
    $scope.root_dir = '/var/www/example.local';
    $scope.directory_as_server_name = true;
    $scope.public_dir = '/www';
    $scope.engine = $scope.engines[0];

    var directorAsServerName = function() {
        if ($scope.directory_as_server_name) {
            var root_dir = $scope.root_dir.split('/');
            root_dir[root_dir.length - 1] = $scope.server_name;
            $scope.root_dir = root_dir.join('/');
        }
    };

    $scope.$watch('server_name', function() {
        directorAsServerName();
    });

    $scope.$watch('directory_as_server_name', function() {
        directorAsServerName();
    });

    $scope.addHost = function() {
        $http({
            method: 'POST',
            data: JSON.stringify({
                server_name: $scope.server_name,
                root_dir: $scope.root_dir,
                user: $scope.user,
                public_dir: $scope.public_dir,
                engine: $scope.engine.id
            }),
            headers: {'Content-Type': 'application/json'},
            url: '/api/addhost'
        }).
            success(function(data, status, headers, config) {
                $location.path('/hosts/')
            }).
            error(function(data, status, headers, config) {
            });
    }
}

function HostDeleteCtrl($scope, $http, $routeParams, $location) {
    $scope.server_name = $routeParams.server_name;

//    $scope.$watch('server_name', function() {
//        if ($scope.directory_as_server_name) {
//            $scope.root_dir = $scope.user;
//        }
//    });

    $scope.deleteHost = function() {
        $http({
            method: 'POST',
            data: JSON.stringify({
                server_name: $scope.server_name
            }),
            headers: {'Content-Type': 'application/json'},
            url: '/api/deletehost'
        }).
            success(function(data, status, headers, config) {
                $location.path('/hosts/')
            }).
            error(function(data, status, headers, config) {
            });
    }
}