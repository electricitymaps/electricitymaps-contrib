var exports = module.exports = {};

exports.stringFormat = function(str) {
    var args = arguments;
        return str.replace(/{(\d+)}/g, function(match, number) { 
            return typeof args[number] != 'undefined'
                ? args[number]
                : match;
    });
};
