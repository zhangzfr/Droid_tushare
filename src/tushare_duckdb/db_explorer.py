"""
DuckDB Database Explorer - 数据库管理工具
集成到 tushare_duckdb 主程序中的数据库浏览和管理功能
"""
import duckdb
import os
from typing import List, Optional, Tuple
from .config import API_CONFIG


class DuckDBExplorer:
    """DuckDB 数据库浏览器类"""
    
    def __init__(self, db_files: List[str] = None):
        """
        初始化浏览器
        
        Args:
            db_files: 数据库文件路径列表，如果为 None 则自动从 API_CONFIG 获取
        """
        if db_files is None:
            self.db_files = self._get_db_files_from_config()
        else:
            self.db_files = db_files
        self.current_db: Optional[str] = None
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def _get_db_files_from_config(self) -> List[str]:
        """从 API_CONFIG 获取所有数据库文件路径"""
        db_files = set()
        for category, config in API_CONFIG.items():
            if isinstance(config, dict) and 'db_path' in config:
                db_path = config['db_path']
                if db_path and os.path.exists(db_path):
                    db_files.add(db_path)
        return sorted(list(db_files))

    def list_databases(self) -> List[str]:
        """列出所有可用数据库"""
        print("\n可用数据库文件：")
        for i, db_file in enumerate(self.db_files, 1):
            exists = "✓" if os.path.exists(db_file) else "✗"
            print(f"{i:>2}. [{exists}] {os.path.basename(db_file)}")
        return self.db_files

    def connect_to_db(self, db_index: int) -> bool:
        """
        连接到指定数据库
        
        Args:
            db_index: 数据库索引（从0开始）
            
        Returns:
            是否连接成功
        """
        if 0 <= db_index < len(self.db_files):
            if self.conn:
                self.conn.close()
            db_path = self.db_files[db_index]
            if not os.path.exists(db_path):
                print(f"数据库文件不存在: {db_path}")
                return False
            self.conn = duckdb.connect(db_path, read_only=True)
            self.current_db = os.path.basename(db_path)
            print(f"\n已连接到: {self.current_db}")
            return True
        else:
            print("无效的数据库索引")
            return False

    def list_tables(self) -> List[Tuple[str, int]]:
        """
        列出当前数据库中的所有表
        
        Returns:
            表名和记录数的列表
        """
        if not self.conn:
            print("请先选择一个数据库")
            return []

        tables = self.conn.execute("SHOW TABLES").fetchall()
        if not tables:
            print("当前数据库中没有表")
            return []

        print(f"\n{self.current_db} 中的表：")
        result = []
        for i, table in enumerate(tables, 1):
            table_name = table[0]
            try:
                count = self.conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]
                print(f"{i:>3}. {table_name:<30} (记录数: {count:>12,})")
                result.append((table_name, count))
            except Exception as e:
                error_type = type(e).__name__
                print(f"{i:>3}. {table_name:<30} (错误: {error_type} - 可能是递归视图或损坏的表)")
                result.append((table_name, -1))
        return result

    def show_table_schema(self, table_name: str):
        """
        显示表结构
        
        Args:
            table_name: 表名
        """
        if not self.conn:
            print("请先选择一个数据库")
            return

        try:
            # 获取表结构
            columns = self.conn.execute(f"DESCRIBE \"{table_name}\"").fetchall()

            # 获取主键信息
            pk_query = f"""
                SELECT column_name 
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                 AND tc.table_name = kcu.table_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_name = '{table_name}'
                ORDER BY kcu.ordinal_position
            """
            pk_result = self.conn.execute(pk_query).fetchall()
            primary_keys = [row[0] for row in pk_result] if pk_result else []

            print(f"\n表 {table_name} 的结构：")
            print("-" * 60)
            print(f"{'字段名称':<20} | {'数据类型':<18} | {'是否主键':<8}")
            print("-" * 60)
            for col in columns:
                col_name = col[0]
                col_type = col[1]
                is_pk = "是" if col_name in primary_keys else ""
                print(f"{col_name:<20} | {col_type:<18} | {is_pk:<8}")
            print("-" * 60)

            if primary_keys:
                print(f"主键：{', '.join(primary_keys)}")
            else:
                print("无主键")

            count = self.conn.execute(f"SELECT COUNT(*) FROM \"{table_name}\"").fetchone()[0]
            print(f"记录总数: {count:,}")

        except Exception as e:
            print(f"错误: {str(e)}")

    def show_sample_data(self, table_name: str, limit: int = 10):
        """
        预览表数据
        
        Args:
            table_name: 表名
            limit: 显示行数
        """
        if not self.conn:
            print("请先选择一个数据库")
            return

        try:
            df = self.conn.execute(f"SELECT * FROM \"{table_name}\" LIMIT {limit}").fetchdf()
            print(f"\n表 {table_name} 的前 {limit} 条记录：")
            print(df.to_string())
        except Exception as e:
            print(f"错误: {str(e)}")

    def delete_object(self, object_name: str) -> bool:
        """
        删除表或视图（自动检测类型）
        
        Args:
            object_name: 表或视图名
            
        Returns:
            是否删除成功
        """
        if not self.conn:
            print("请先选择一个数据库")
            return False

        # 需要写入权限，重新连接
        db_path = None
        for path in self.db_files:
            if os.path.basename(path) == self.current_db:
                db_path = path
                break
        
        if not db_path:
            print("无法找到当前数据库路径")
            return False

        try:
            # 关闭只读连接，打开写入连接
            self.conn.close()
            write_conn = duckdb.connect(db_path, read_only=False)

            # 检查是否为视图
            view_check = write_conn.execute(
                f"SELECT COUNT(*) FROM information_schema.views WHERE table_name = '{object_name}'"
            ).fetchone()[0]

            if view_check > 0:
                write_conn.execute(f"DROP VIEW \"{object_name}\"")
                print(f"视图 {object_name} 已删除")
            else:
                # 检查是否为表
                table_check = write_conn.execute(
                    f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{object_name}'"
                ).fetchone()[0]

                if table_check > 0:
                    write_conn.execute(f"DROP TABLE \"{object_name}\"")
                    print(f"表 {object_name} 已删除")
                else:
                    print(f"未找到名为 {object_name} 的表或视图")
                    write_conn.close()
                    # 恢复只读连接
                    self.conn = duckdb.connect(db_path, read_only=True)
                    return False

            write_conn.close()
            # 恢复只读连接
            self.conn = duckdb.connect(db_path, read_only=True)
            return True

        except Exception as e:
            print(f"错误: {str(e)}")
            # 尝试恢复连接
            try:
                self.conn = duckdb.connect(db_path, read_only=True)
            except:
                self.conn = None
            return False

    def execute_query(self, query: str):
        """
        执行自定义 SQL 查询
        
        Args:
            query: SQL 查询语句
        """
        if not self.conn:
            print("请先选择一个数据库")
            return

        try:
            result = self.conn.execute(query).fetchdf()
            print(f"\n查询结果 ({len(result)} 行)：")
            if len(result) > 50:
                print(result.head(50).to_string())
                print(f"... 共 {len(result)} 行，只显示前 50 行")
            else:
                print(result.to_string())
        except Exception as e:
            print(f"查询错误: {str(e)}")

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


def run_explorer():
    """运行数据库浏览器交互界面"""
    explorer = DuckDBExplorer()

    if not explorer.db_files:
        print("错误：未找到任何数据库文件！")
        print("请检查 settings.yaml 中的数据库路径配置。")
        return

    while True:
        print("\n" + "=" * 60)
        print("       DuckDB 数据库管理工具")
        print("=" * 60)
        print("命令选项：")
        print("  1. 列出所有数据库")
        print("  2. 选择/切换数据库")
        print("  3. 列出当前数据库中的表")
        print("  4. 查看表结构")
        print("  5. 预览表数据")
        print("  6. 删除表/视图")
        print("  7. 执行自定义 SQL")
        print("  0. 返回主菜单")
        
        if explorer.current_db:
            print(f"\n当前数据库: {explorer.current_db}")

        choice = input("\n请输入你的选择: ").strip()

        if choice == "0":
            explorer.close()
            print("已退出数据库管理工具")
            break

        elif choice == "1":
            explorer.list_databases()

        elif choice == "2":
            explorer.list_databases()
            try:
                db_index = int(input("请输入数据库编号 (从1开始): ").strip()) - 1
                explorer.connect_to_db(db_index)
            except ValueError:
                print("请输入有效的数字")

        elif choice == "3":
            explorer.list_tables()

        elif choice == "4":
            if not explorer.conn:
                print("请先选择一个数据库（选项 2）")
                continue
            table_name = input("请输入表名: ").strip()
            if table_name:
                explorer.show_table_schema(table_name)

        elif choice == "5":
            if not explorer.conn:
                print("请先选择一个数据库（选项 2）")
                continue
            table_name = input("请输入表名: ").strip()
            if table_name:
                limit_str = input("显示行数（默认 10）: ").strip()
                limit = int(limit_str) if limit_str.isdigit() else 10
                explorer.show_sample_data(table_name, limit)

        elif choice == "6":
            if not explorer.conn:
                print("请先选择一个数据库（选项 2）")
                continue
            object_name = input("请输入要删除的表或视图名: ").strip()
            if object_name:
                confirm = input(f"确定要删除 {object_name} 吗？此操作不可恢复！(y/n): ").strip()
                if confirm.lower() == 'y':
                    explorer.delete_object(object_name)

        elif choice == "7":
            if not explorer.conn:
                print("请先选择一个数据库（选项 2）")
                continue
            print("请输入 SQL 查询（只支持 SELECT 查询）：")
            query = input("SQL> ").strip()
            if query:
                if query.upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                    explorer.execute_query(query)
                else:
                    print("安全限制：只允许执行 SELECT/SHOW/DESCRIBE/EXPLAIN 查询")

        else:
            print("无效的选择，请输入 0-7 之间的数字")


if __name__ == "__main__":
    run_explorer()
