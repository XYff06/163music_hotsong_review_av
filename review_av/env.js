window = global;
delete global;
delete Buffer;
document = {};
location = {};
element = {};
screen = {};
navigator = {};
history = {};

function MonitorObjectProperties(targetObjects) {
    for (let index = 0; index < targetObjects.length; index++) {
        const currentTarget = targetObjects[index];
        const propertyList = Object.keys(currentTarget);

        propertyList.forEach(propName => {
            const propertyValue = currentTarget[propName];

            if (propertyValue && typeof propertyValue === 'object') {
                currentTarget[propName] = new Proxy(propertyValue, {
                    get(obj, propKey, receiver) {
                        const resultValue = Reflect.get(obj, propKey, receiver);
                        console.log(`操作类型：get，目标对象：${propName}，访问属性：${propKey}，属性标识类型：${typeof propKey}，获取数值：${resultValue}，数值类型：${typeof resultValue}`);
                        return resultValue;
                    },
                    set(obj, propKey, updatedValue, receiver) {
                        console.log(`操作类型：set，目标对象：${propName}，修改属性：${propKey}，属性标识类型：${typeof propKey}，新赋值：${updatedValue}，数值类型：${typeof updatedValue}`);
                        return Reflect.set(obj, propKey, updatedValue, receiver);
                    }
                });
            }
        });
    }
}

const systemComponents = [window, document, location, element, screen, navigator, history,];
MonitorObjectProperties(systemComponents);
