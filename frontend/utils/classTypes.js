export const CLASS_TYPE_OPTIONS = [
  { label: 'VIP', value: 'VIP' },
  { label: '小班', value: '小班' },
  { label: '一对二', value: '一对二' }
]

const CREATE_CLASS_TYPE_VALUES = CLASS_TYPE_OPTIONS.map(function(item) {
  return item.value
})

export const isCreateClassType = function(classType) {
  return CREATE_CLASS_TYPE_VALUES.indexOf(String(classType || '').trim()) > -1
}
