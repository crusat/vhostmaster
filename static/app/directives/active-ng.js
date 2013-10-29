'use strict';

angular.module('active-ng', []).
    directive('active', ['$location', function (location) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs, controller) {
                attrs.$observe('active', function(active) {
                    scope.active = active;
                    scope.location = location;

                });
                var clazz = 'active';
                scope.$watch('location.path()', function (newPath) {
                    if (scope.active === newPath) {
                        element.addClass(clazz);
                    } else {
                        element.removeClass(clazz);
                    }
                });


            }

        };

    }]);